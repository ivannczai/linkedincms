#!/usr/bin/env python
"""
Script to set up initial data for the Winning Sales Content Hub.
This script will:
1. Create an admin user
2. Create a client user
3. Add sample strategies and content pieces
"""

import os
import sys
import subprocess
import json
import requests
import time

# Configuration
BACKEND_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"
CLIENT_EMAIL = "client@example.com"
CLIENT_PASSWORD = "client123"
CLIENT_COMPANY = "Acme Corporation"
CLIENT_INDUSTRY = "Technology"
CLIENT_CONTACT = "John Doe"

def run_command(command):
    """Run a command and print its output."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result

def create_admin_user():
    """Create an admin user using the create_admin.py script."""
    print("\n=== Creating Admin User ===")
    cmd = f"cd backend && python scripts/create_admin.py {ADMIN_EMAIL} {ADMIN_PASSWORD}"
    run_command(cmd)

def create_client_user():
    """Create a client user using the create_client.py script."""
    print("\n=== Creating Client User ===")
    cmd = f"cd backend && python scripts/create_client.py {CLIENT_EMAIL} {CLIENT_PASSWORD} \"{CLIENT_COMPANY}\" \"{CLIENT_INDUSTRY}\" \"{CLIENT_CONTACT}\""
    run_command(cmd)

def get_auth_token(email, password):
    """Get an authentication token for the given user."""
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code != 200:
        print(f"Failed to get auth token: {response.text}")
        return None
    return response.json().get("access_token")

def add_sample_strategy(token, client_id):
    """Add a sample strategy for the client."""
    print("\n=== Adding Sample Strategy ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get client ID if not provided
    if not client_id:
        response = requests.get(f"{BACKEND_URL}/api/v1/clients/", headers=headers)
        if response.status_code != 200:
            print(f"Failed to get clients: {response.text}")
            return
        clients = response.json()
        if not clients:
            print("No clients found")
            return
        client_id = clients[0]["id"]
    
    # Create strategy
    strategy_data = {
        "title": "2025 Market Expansion Strategy",
        "details": """# Market Expansion Strategy

## Executive Summary
This strategy outlines our approach to expanding into new markets in 2025.

## Target Markets
1. North America
2. Europe
3. Asia Pacific

## Key Initiatives
* Establish local partnerships
* Adapt products to regional needs
* Implement targeted marketing campaigns

## Success Metrics
* 30% increase in market share
* 25% revenue growth
* 20% increase in customer base
""",
        "client_id": client_id,
        "is_active": True
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/strategies/",
        json=strategy_data,
        headers=headers
    )
    
    if response.status_code == 200 or response.status_code == 201:
        print(f"Strategy created successfully: {response.json()}")
        return response.json().get("id")
    else:
        print(f"Failed to create strategy: {response.text}")
        return None

def add_sample_content(token, strategy_id):
    """Add sample content pieces for the strategy."""
    print("\n=== Adding Sample Content Pieces ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    content_pieces = [
        {
            "title": "Market Analysis Report",
            "content_type": "DOCUMENT",
            "description": "Comprehensive analysis of target markets",
            "content": """# Market Analysis Report

## Overview
This report provides a detailed analysis of our target markets for 2025.

## Market Size
* North America: $2.5B
* Europe: $1.8B
* Asia Pacific: $3.2B

## Competitive Landscape
* Major competitors in each region
* Market share analysis
* Competitive advantages and disadvantages

## Recommendations
Based on our analysis, we recommend prioritizing the Asia Pacific region due to its larger market size and growth potential.
""",
            "strategy_id": strategy_id,
            "is_approved": True
        },
        {
            "title": "Sales Presentation Deck",
            "content_type": "PRESENTATION",
            "description": "Presentation for potential clients",
            "content": """# Sales Presentation

## Our Company
* Founded in 2010
* Industry leader in innovative solutions
* Global presence with local expertise

## Our Solutions
* Product A: Enterprise management
* Product B: Data analytics
* Product C: Cloud integration

## Why Choose Us
* Proven track record
* Dedicated support team
* Customizable solutions
* Competitive pricing
""",
            "strategy_id": strategy_id,
            "is_approved": True
        },
        {
            "title": "Email Campaign Template",
            "content_type": "EMAIL",
            "description": "Template for outreach emails",
            "content": """# Email Campaign Template

## Subject Line
Revolutionize Your Business with Our Solutions

## Body
Dear [Client Name],

I hope this email finds you well. I'm reaching out because I believe our solutions can help [Company Name] achieve its business objectives.

Our clients have seen:
* 30% increase in efficiency
* 25% reduction in costs
* 20% improvement in customer satisfaction

Would you be available for a 15-minute call next week to discuss how we can help your business?

Best regards,
[Sales Rep Name]
""",
            "strategy_id": strategy_id,
            "is_approved": True
        }
    ]
    
    for content in content_pieces:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/contents/",
            json=content,
            headers=headers
        )
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"Content piece created successfully: {response.json().get('title')}")
        else:
            print(f"Failed to create content piece: {response.text}")

def main():
    """Main function to set up initial data."""
    print("=== Setting up initial data for Winning Sales Content Hub ===")
    
    # Wait for backend to be ready
    print("Waiting for backend to be ready...")
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get(f"{BACKEND_URL}/api/v1/")
            if response.status_code == 200:
                print("Backend is ready!")
                break
        except requests.exceptions.ConnectionError:
            print(f"Backend not ready yet. Retry {i+1}/{max_retries}...")
            time.sleep(2)
    
    # Create users
    create_admin_user()
    create_client_user()
    
    # Get admin token
    admin_token = get_auth_token(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not admin_token:
        print("Failed to get admin token. Exiting.")
        return
    
    # Add sample data
    client_id = None  # Will be fetched in add_sample_strategy
    strategy_id = add_sample_strategy(admin_token, client_id)
    if strategy_id:
        add_sample_content(admin_token, strategy_id)
    
    print("\n=== Setup Complete ===")
    print(f"Admin user: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"Client user: {CLIENT_EMAIL} / {CLIENT_PASSWORD}")
    print("You can now log in to the application with these credentials.")

if __name__ == "__main__":
    main()
