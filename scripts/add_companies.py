#!/usr/bin/env python3
"""
Add companies to companies.csv from incoming.csv or stdin.

This script:
- Normalizes URLs (force https://, strip trailing slashes)
- Generates id as slug(name)-slug(city)
- Validates enums (industry, remote_policy, province)
- Dedupes against existing companies.csv
- Geocodes city, province, Canada → lat/lng
- Caches geocoding results locally

Usage:
    python scripts/add_companies.py [--check] [--input data/incoming.csv]
    
    --check: Validate only, don't write to companies.csv
    --input: Path to input CSV (default: data/incoming.csv or stdin)
"""

import csv
import sys
import os
import json
import re
import argparse
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
except ImportError:
    print("Error: geopy is required. Install with: pip install geopy")
    sys.exit(1)

# Constants
CSV_PATH = 'companies.csv'
CACHE_PATH = 'data/geocode_cache.json'
INDUSTRIES = {
    'SaaS', 'Fintech', 'Healthtech', 'Ecommerce', 'Agency', 
    'Gaming', 'AI', 'Cleantech', 'Telecommunications'
}
REMOTE_POLICIES = {'Remote', 'Hybrid', 'Onsite'}
PROVINCES = {
    'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 
    'PE', 'QC', 'SK', 'YT'
}

# Geocoder instance (lazy-loaded)
_geocoder = None

def get_geocoder():
    """Get or create geocoder instance."""
    global _geocoder
    if _geocoder is None:
        _geocoder = Nominatim(user_agent="canada-tech-repo")
    return _geocoder

def load_cache() -> Dict[str, Dict[str, float]]:
    """Load geocoding cache from JSON file."""
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_cache(cache: Dict[str, Dict[str, float]]):
    """Save geocoding cache to JSON file."""
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)

def normalize_url(url: str) -> str:
    """Normalize URL: force https://, strip trailing slashes."""
    url = url.strip()
    if not url:
        return url
    
    # Add https:// if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    elif url.startswith('http://'):
        url = url.replace('http://', 'https://', 1)
    
    # Strip trailing slash
    url = url.rstrip('/')
    
    return url

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and special chars with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text

def generate_id(name: str, city: str) -> str:
    """Generate id as slug(name)-slug(city)."""
    name_slug = slugify(name)
    city_slug = slugify(city)
    return f"{name_slug}-{city_slug}"

def geocode_location(city: str, province: str, hq_address: Optional[str] = None) -> Tuple[float, float]:
    """
    Geocode city, province, Canada to lat/lng.
    Uses cache to avoid repeated API calls.
    Returns (lat, lng) tuple.
    Raises ValueError if geocoding fails.
    """
    cache = load_cache()
    
    # Build query
    query_parts = []
    if hq_address:
        query_parts.append(hq_address)
    query_parts.append(city)
    query_parts.append(province)
    query_parts.append('Canada')
    query = ', '.join(query_parts)
    
    # Check cache
    cache_key = f"{city}, {province}, Canada"
    if cache_key in cache:
        cached = cache[cache_key]
        return cached['lat'], cached['lng']
    
    # Geocode
    try:
        geocoder = get_geocoder()
        location = geocoder.geocode(query, timeout=10)
        
        if location is None:
            raise ValueError(f"Geocoding failed for: {query}")
        
        lat, lng = location.latitude, location.longitude
        
        # Cache result
        cache[cache_key] = {'lat': lat, 'lng': lng}
        save_cache(cache)
        
        return lat, lng
        
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        raise ValueError(f"Geocoding error for {query}: {e}")

def load_existing_companies() -> List[Dict[str, str]]:
    """Load existing companies from companies.csv."""
    if not os.path.exists(CSV_PATH):
        return []
    
    companies = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append(row)
    
    return companies

def normalize_name(name: str) -> str:
    """Normalize company name for deduplication."""
    # Lowercase, strip, remove common suffixes
    name = name.strip().lower()
    # Remove common corporate suffixes for comparison
    suffixes = [' inc.', ' inc', ' ltd.', ' ltd', ' corp.', ' corp', ' llc', ' co.', ' co']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    return name

def is_duplicate(new_company: Dict[str, str], existing_companies: List[Dict[str, str]]) -> bool:
    """
    Check if company is duplicate based on:
    - Same id, OR
    - Same normalized name + city + province
    """
    new_id = new_company['id']
    new_name_norm = normalize_name(new_company['name'])
    new_city = new_company['city'].strip().lower()
    new_province = new_company['province'].strip().upper()
    
    for existing in existing_companies:
        # Check ID match
        if existing.get('id') == new_id:
            return True
        
        # Check name + city + province match
        existing_name_norm = normalize_name(existing.get('name', ''))
        existing_city = existing.get('city', '').strip().lower()
        existing_province = existing.get('province', '').strip().upper()
        
        if (existing_name_norm == new_name_norm and 
            existing_city == new_city and 
            existing_province == new_province):
            return True
    
    return False

def validate_company(company: Dict[str, str]) -> List[str]:
    """Validate a company record. Returns list of errors (empty if valid)."""
    errors = []
    
    # Required fields
    required = ['name', 'url', 'industry', 'remote_policy', 'city', 'province']
    for field in required:
        if not company.get(field) or not company[field].strip():
            errors.append(f"Missing required field: {field}")
    
    # URL validation
    if company.get('url'):
        url = normalize_url(company['url'])
        if not url.startswith('https://'):
            errors.append(f"URL must start with https://: {company['url']}")
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                errors.append(f"Invalid URL format: {company['url']}")
        except Exception as e:
            errors.append(f"Invalid URL: {company['url']} ({e})")
    
    # Industry enum validation
    if company.get('industry'):
        industry = company['industry'].strip()
        if industry not in INDUSTRIES:
            errors.append(f"Invalid industry '{industry}'. Must be one of: {', '.join(sorted(INDUSTRIES))}")
    
    # Remote policy enum validation
    if company.get('remote_policy'):
        policy = company['remote_policy'].strip()
        if policy not in REMOTE_POLICIES:
            errors.append(f"Invalid remote_policy '{policy}'. Must be one of: {', '.join(sorted(REMOTE_POLICIES))}")
    
    # Province enum validation
    if company.get('province'):
        province = company['province'].strip().upper()
        if province not in PROVINCES:
            errors.append(f"Invalid province '{province}'. Must be one of: {', '.join(sorted(PROVINCES))}")
    
    return errors

def process_incoming_companies(input_path: Optional[str] = None, check_only: bool = False) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Process incoming companies from CSV file or stdin.
    Returns (processed_companies, errors) tuple.
    """
    errors = []
    incoming_companies = []
    
    # Read input
    if input_path:
        if not os.path.exists(input_path):
            errors.append(f"Input file not found: {input_path}")
            return [], errors
        input_file = open(input_path, 'r', encoding='utf-8')
    else:
        # Try data/incoming.csv, fallback to stdin
        if os.path.exists('data/incoming.csv'):
            input_file = open('data/incoming.csv', 'r', encoding='utf-8')
        else:
            input_file = sys.stdin
    
    try:
        reader = csv.DictReader(input_file)
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            # Skip empty rows
            if not any(row.values()):
                continue
            
            # Skip comment rows (starting with #)
            if row.get('name', '').strip().startswith('#'):
                continue
            
            incoming_companies.append(row)
    finally:
        if input_file != sys.stdin:
            input_file.close()
    
    if not incoming_companies:
        errors.append("No companies found in input")
        return [], errors
    
    # Load existing companies
    existing_companies = load_existing_companies()
    
    # Process each company
    processed = []
    for idx, company in enumerate(incoming_companies):
        # Validate
        validation_errors = validate_company(company)
        if validation_errors:
            errors.extend([f"Row {idx + 2}: {e}" for e in validation_errors])
            continue
        
        # Normalize URL
        company['url'] = normalize_url(company['url'])
        
        # Generate ID
        company['id'] = generate_id(company['name'], company['city'])
        
        # Normalize province to uppercase
        company['province'] = company['province'].strip().upper()
        
        # Check for duplicates against existing companies
        if is_duplicate(company, existing_companies):
            errors.append(f"Duplicate company: {company['name']} in {company['city']}, {company['province']} (id: {company['id']})")
            continue
        
        # Check for duplicates within the same batch
        if is_duplicate(company, processed):
            errors.append(f"Duplicate company in batch: {company['name']} in {company['city']}, {company['province']} (id: {company['id']})")
            continue
        
        # Geocode
        try:
            hq_address = company.get('hq_address', '').strip() or None
            lat, lng = geocode_location(company['city'], company['province'], hq_address)
            company['lat'] = str(lat)
            company['lng'] = str(lng)
        except ValueError as e:
            errors.append(f"Geocoding failed for {company['name']} ({company['city']}, {company['province']}): {e}")
            continue
        
        # Set optional fields with defaults
        company['description'] = company.get('description', '').strip()
        company['tags'] = company.get('tags', '').strip()
        
        processed.append(company)
    
    # If check_only, don't write
    if check_only:
        return processed, errors
    
    # If there are errors, don't write anything
    if errors:
        return processed, errors
    
    # Append to companies.csv
    if processed:
        # Read existing to get all columns
        fieldnames = ['id', 'name', 'url', 'description', 'industry', 'tags', 'remote_policy', 'city', 'province', 'lat', 'lng']
        
        # Load all existing companies
        all_companies = existing_companies + processed
        
        # Sort by province then name
        all_companies.sort(key=lambda x: (x.get('province', ''), x.get('name', '')))
        
        # Write back
        with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for company in all_companies:
                writer.writerow({k: company.get(k, '') for k in fieldnames})
    
    return processed, errors

def main():
    parser = argparse.ArgumentParser(
        description='Add companies to companies.csv from incoming.csv or stdin',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Validate only, do not write to companies.csv'
    )
    parser.add_argument(
        '--input',
        type=str,
        help='Path to input CSV file (default: data/incoming.csv or stdin)'
    )
    
    args = parser.parse_args()
    
    processed, errors = process_incoming_companies(args.input, check_only=args.check)
    
    if errors:
        print("Errors found:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    
    if args.check:
        print(f"✓ Validation passed: {len(processed)} company(ies) would be added")
    else:
        print(f"✓ Successfully added {len(processed)} company(ies) to {CSV_PATH}")
        for company in processed:
            print(f"  - {company['name']} ({company['city']}, {company['province']})")

if __name__ == '__main__':
    main()

