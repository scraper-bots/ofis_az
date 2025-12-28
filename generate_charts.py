#!/usr/bin/env python3
"""
Business Analysis Chart Generator for Real Estate Listings
Generates business-focused visualizations for executive decision-making
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os
from pathlib import Path

# Set style for professional-looking charts
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

# Create output directory
CHARTS_DIR = Path("charts")
CHARTS_DIR.mkdir(exist_ok=True)

def clean_price(price_str):
    """Extract numeric price from price string"""
    if pd.isna(price_str):
        return None
    # Extract numbers from strings like "24000 Azn" or "4300 Azn / Ay"
    match = re.search(r'([\d\s]+)', str(price_str))
    if match:
        return float(match.group(1).replace(' ', ''))
    return None

def clean_area(area_str):
    """Extract numeric area from area string"""
    if pd.isna(area_str):
        return None
    # Extract numbers from strings like "44 m²"
    match = re.search(r'(\d+)', str(area_str))
    if match:
        return float(match.group(1))
    return None

def extract_property_type(category_str):
    """Extract main property type from category"""
    if pd.isna(category_str):
        return "Other"

    category = str(category_str)
    if "Həyət evləri" in category or "evləri" in category:
        return "House"
    elif "Yeni tikili" in category:
        return "New Construction"
    elif "Köhnə tikili" in category:
        return "Old Construction"
    elif "Obyektlər" in category or "Ofislər" in category:
        return "Commercial"
    elif "Bağ" in category:
        return "Garden/Dacha"
    elif "Torpaq" in category:
        return "Land"
    else:
        return "Other"

def extract_transaction_type(category_str):
    """Extract transaction type (Sale/Rent)"""
    if pd.isna(category_str):
        return "Unknown"

    category = str(category_str)
    if "Satılır" in category:
        return "For Sale"
    elif "icarə" in category or "İcarə" in category:
        return "For Rent"
    else:
        return "Unknown"

def load_and_prepare_data():
    """Load and clean the dataset"""
    print("Loading data...")
    df = pd.read_csv('ofis_listings.csv')

    print(f"Total listings loaded: {len(df):,}")

    # Clean and prepare data
    df['price_clean'] = df['price'].apply(clean_price)
    df['area_clean'] = df['Sahə'].apply(clean_area)
    df['property_type'] = df['category'].apply(extract_property_type)
    df['transaction_type'] = df['category'].apply(extract_transaction_type)

    # Calculate price per sqm
    df['price_per_sqm'] = df.apply(
        lambda row: row['price_clean'] / row['area_clean']
        if pd.notna(row['price_clean']) and pd.notna(row['area_clean']) and row['area_clean'] > 0
        else None,
        axis=1
    )

    # Clean city names
    df['city_clean'] = df['Şəhər'].fillna('Unknown')

    # Extract district from category or title
    def extract_district(row):
        text = str(row.get('category', '')) + ' ' + str(row.get('title', ''))
        districts = ['Yasamal', 'Nəsimi', 'Binəqədi', 'Nərimanov', 'Sabunçu',
                    'Xətai', 'Səbail', 'Suraxanı', 'Abşeron', 'Nizami', 'Qaradağ']
        for district in districts:
            if district in text:
                return district
        return 'Other'

    df['district'] = df.apply(extract_district, axis=1)

    print("Data preparation complete.")
    return df

def generate_chart_1_transaction_volume(df):
    """Chart 1: Transaction Volume by Type"""
    print("Generating Chart 1: Transaction Volume by Type...")

    trans_counts = df['transaction_type'].value_counts()

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#2ecc71', '#3498db', '#95a5a6']
    bars = ax.bar(trans_counts.index, trans_counts.values, color=colors)

    ax.set_title('Listing Volume by Transaction Type', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Transaction Type', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Listings', fontsize=12, fontweight='bold')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '01_transaction_volume.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Chart 1 saved")

def generate_chart_2_property_type_distribution(df):
    """Chart 2: Property Type Distribution"""
    print("Generating Chart 2: Property Type Distribution...")

    prop_counts = df['property_type'].value_counts().head(8)

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = sns.color_palette("Set2", len(prop_counts))
    bars = ax.barh(prop_counts.index, prop_counts.values, color=colors)

    ax.set_title('Inventory Distribution by Property Type', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Number of Listings', fontsize=12, fontweight='bold')
    ax.set_ylabel('Property Type', fontsize=12, fontweight='bold')

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, prop_counts.values)):
        ax.text(val, bar.get_y() + bar.get_height()/2.,
                f' {int(val):,}',
                va='center', fontweight='bold')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '02_property_type_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Chart 2 saved")

def generate_chart_3_price_distribution(df):
    """Chart 3: Price Distribution by Property Type"""
    print("Generating Chart 3: Price Distribution by Property Type...")

    # Filter for sale properties with valid prices
    sale_df = df[(df['transaction_type'] == 'For Sale') &
                 (df['price_clean'].notna()) &
                 (df['price_clean'] > 0) &
                 (df['price_clean'] < 1000000)]  # Remove outliers

    # Get top property types
    top_types = sale_df['property_type'].value_counts().head(5).index
    plot_df = sale_df[sale_df['property_type'].isin(top_types)]

    fig, ax = plt.subplots(figsize=(12, 6))

    # Create box plot
    positions = range(len(top_types))
    bp = ax.boxplot([plot_df[plot_df['property_type'] == pt]['price_clean'].values
                      for pt in top_types],
                     labels=top_types,
                     patch_artist=True,
                     showfliers=False)

    # Color the boxes
    colors = sns.color_palette("Set3", len(top_types))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)

    ax.set_title('Price Distribution by Property Type (For Sale)',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Property Type', fontsize=12, fontweight='bold')
    ax.set_ylabel('Price (AZN)', fontsize=12, fontweight='bold')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000)}K'))

    plt.xticks(rotation=15, ha='right')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '03_price_distribution_by_type.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Chart 3 saved")

def generate_chart_4_average_prices(df):
    """Chart 4: Average Prices by Property Type"""
    print("Generating Chart 4: Average Prices by Property Type...")

    sale_df = df[(df['transaction_type'] == 'For Sale') &
                 (df['price_clean'].notna()) &
                 (df['price_clean'] > 0)]

    avg_prices = sale_df.groupby('property_type')['price_clean'].agg(['mean', 'count'])
    avg_prices = avg_prices[avg_prices['count'] >= 10].sort_values('mean', ascending=False).head(8)

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = sns.color_palette("coolwarm", len(avg_prices))
    bars = ax.barh(avg_prices.index, avg_prices['mean'], color=colors)

    ax.set_title('Average Sale Price by Property Type', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Average Price (AZN)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Property Type', fontsize=12, fontweight='bold')
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000)}K'))

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, avg_prices['mean'])):
        ax.text(val, bar.get_y() + bar.get_height()/2.,
                f' {int(val):,} AZN',
                va='center', fontweight='bold')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '04_average_prices_by_type.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Chart 4 saved")

def generate_chart_5_district_volume(df):
    """Chart 5: Listing Volume by District"""
    print("Generating Chart 5: Listing Volume by District...")

    district_counts = df['district'].value_counts().head(10)

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = sns.color_palette("viridis", len(district_counts))
    bars = ax.bar(district_counts.index, district_counts.values, color=colors)

    ax.set_title('Top 10 Districts by Listing Volume', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('District', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Listings', fontsize=12, fontweight='bold')

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontweight='bold')

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '05_district_volume.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Chart 5 saved")

def generate_chart_6_district_prices(df):
    """Chart 6: Average Prices by District"""
    print("Generating Chart 6: Average Prices by District...")

    sale_df = df[(df['transaction_type'] == 'For Sale') &
                 (df['price_clean'].notna()) &
                 (df['price_clean'] > 0)]

    district_prices = sale_df.groupby('district')['price_clean'].agg(['mean', 'count'])
    district_prices = district_prices[district_prices['count'] >= 20].sort_values('mean', ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = sns.color_palette("rocket", len(district_prices))
    bars = ax.barh(district_prices.index, district_prices['mean'], color=colors)

    ax.set_title('Average Sale Price by District (Top 10)', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Average Price (AZN)', fontsize=12, fontweight='bold')
    ax.set_ylabel('District', fontsize=12, fontweight='bold')
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000)}K'))

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, district_prices['mean'])):
        ax.text(val, bar.get_y() + bar.get_height()/2.,
                f' {int(val):,} AZN',
                va='center', fontweight='bold')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '06_district_average_prices.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Chart 6 saved")

def generate_chart_7_price_per_sqm(df):
    """Chart 7: Price per Square Meter by Property Type"""
    print("Generating Chart 7: Price per Square Meter...")

    sale_df = df[(df['transaction_type'] == 'For Sale') &
                 (df['price_per_sqm'].notna()) &
                 (df['price_per_sqm'] > 0) &
                 (df['price_per_sqm'] < 10000)]  # Remove outliers

    type_sqm = sale_df.groupby('property_type')['price_per_sqm'].agg(['mean', 'count'])
    type_sqm = type_sqm[type_sqm['count'] >= 10].sort_values('mean', ascending=False).head(8)

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = sns.color_palette("mako", len(type_sqm))
    bars = ax.barh(type_sqm.index, type_sqm['mean'], color=colors)

    ax.set_title('Average Price per Square Meter by Property Type',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Price per m² (AZN)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Property Type', fontsize=12, fontweight='bold')

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, type_sqm['mean'])):
        ax.text(val, bar.get_y() + bar.get_height()/2.,
                f' {int(val):,} AZN/m²',
                va='center', fontweight='bold')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '07_price_per_sqm.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Chart 7 saved")

def generate_chart_8_room_distribution(df):
    """Chart 8: Distribution by Number of Rooms"""
    print("Generating Chart 8: Room Distribution...")

    room_df = df[df['Otaq Sayı'].notna()].copy()
    room_df['rooms'] = pd.to_numeric(room_df['Otaq Sayı'], errors='coerce')
    room_df = room_df[(room_df['rooms'] >= 1) & (room_df['rooms'] <= 6)]

    room_counts = room_df['rooms'].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = sns.color_palette("Set2", len(room_counts))
    bars = ax.bar(room_counts.index.astype(int), room_counts.values, color=colors, width=0.6)

    ax.set_title('Listing Distribution by Number of Rooms', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Number of Rooms', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Listings', fontsize=12, fontweight='bold')
    ax.set_xticks(range(1, 7))

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '08_room_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Chart 8 saved")

def generate_chart_9_price_by_rooms(df):
    """Chart 9: Average Price by Number of Rooms"""
    print("Generating Chart 9: Price by Room Count...")

    room_df = df[(df['transaction_type'] == 'For Sale') &
                 (df['Otaq Sayı'].notna()) &
                 (df['price_clean'].notna()) &
                 (df['price_clean'] > 0)].copy()

    room_df['rooms'] = pd.to_numeric(room_df['Otaq Sayı'], errors='coerce')
    room_df = room_df[(room_df['rooms'] >= 1) & (room_df['rooms'] <= 6)]

    room_prices = room_df.groupby('rooms')['price_clean'].agg(['mean', 'count'])
    room_prices = room_prices[room_prices['count'] >= 10].sort_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = sns.color_palette("coolwarm", len(room_prices))
    bars = ax.bar(room_prices.index.astype(int), room_prices['mean'], color=colors, width=0.6)

    ax.set_title('Average Sale Price by Number of Rooms', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Number of Rooms', fontsize=12, fontweight='bold')
    ax.set_ylabel('Average Price (AZN)', fontsize=12, fontweight='bold')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000)}K'))
    ax.set_xticks(range(1, 7))

    # Add value labels
    for bar, val in zip(bars, room_prices['mean']):
        ax.text(bar.get_x() + bar.get_width()/2., val,
                f'{int(val/1000)}K',
                ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '09_price_by_rooms.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Chart 9 saved")

def generate_chart_10_area_distribution(df):
    """Chart 10: Property Size Distribution"""
    print("Generating Chart 10: Area Distribution...")

    area_df = df[(df['area_clean'].notna()) &
                 (df['area_clean'] > 0) &
                 (df['area_clean'] <= 300)].copy()

    # Create size categories
    bins = [0, 50, 75, 100, 150, 200, 300]
    labels = ['<50 m²', '50-75 m²', '75-100 m²', '100-150 m²', '150-200 m²', '>200 m²']
    area_df['size_category'] = pd.cut(area_df['area_clean'], bins=bins, labels=labels)

    size_counts = area_df['size_category'].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = sns.color_palette("Spectral", len(size_counts))
    bars = ax.bar(range(len(size_counts)), size_counts.values, color=colors)

    ax.set_title('Property Distribution by Size Category', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Size Category', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Listings', fontsize=12, fontweight='bold')
    ax.set_xticks(range(len(size_counts)))
    ax.set_xticklabels(size_counts.index, rotation=0)

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '10_area_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Chart 10 saved")

def generate_chart_11_rental_market(df):
    """Chart 11: Rental Market Analysis"""
    print("Generating Chart 11: Rental Market Analysis...")

    rent_df = df[(df['transaction_type'] == 'For Rent') &
                 (df['price_clean'].notna()) &
                 (df['price_clean'] > 0)]

    rent_by_type = rent_df.groupby('property_type')['price_clean'].agg(['mean', 'count'])
    rent_by_type = rent_by_type[rent_by_type['count'] >= 5].sort_values('mean', ascending=False).head(8)

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = sns.color_palette("twilight", len(rent_by_type))
    bars = ax.barh(rent_by_type.index, rent_by_type['mean'], color=colors)

    ax.set_title('Average Monthly Rent by Property Type', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Average Monthly Rent (AZN)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Property Type', fontsize=12, fontweight='bold')

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, rent_by_type['mean'])):
        ax.text(val, bar.get_y() + bar.get_height()/2.,
                f' {int(val):,} AZN/month',
                va='center', fontweight='bold')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '11_rental_market_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Chart 11 saved")

def generate_chart_12_price_segments(df):
    """Chart 12: Market Segmentation by Price Range"""
    print("Generating Chart 12: Price Segmentation...")

    sale_df = df[(df['transaction_type'] == 'For Sale') &
                 (df['price_clean'].notna()) &
                 (df['price_clean'] > 0)]

    # Create price segments
    bins = [0, 50000, 100000, 150000, 200000, 300000, 1000000]
    labels = ['<50K', '50-100K', '100-150K', '150-200K', '200-300K', '>300K']
    sale_df['price_segment'] = pd.cut(sale_df['price_clean'], bins=bins, labels=labels)

    segment_counts = sale_df['price_segment'].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = sns.color_palette("RdYlGn_r", len(segment_counts))
    bars = ax.bar(range(len(segment_counts)), segment_counts.values, color=colors)

    ax.set_title('Market Distribution by Price Segment (AZN)', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Price Segment', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Listings', fontsize=12, fontweight='bold')
    ax.set_xticks(range(len(segment_counts)))
    ax.set_xticklabels(segment_counts.index, rotation=0)

    # Add value labels and percentages
    total = segment_counts.sum()
    for bar, val in zip(bars, segment_counts.values):
        height = bar.get_height()
        pct = (val / total) * 100
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(val):,}\n({pct:.1f}%)',
                ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '12_price_segmentation.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Chart 12 saved")

def generate_summary_statistics(df):
    """Generate summary statistics for the README"""
    stats = {}

    # Overall stats
    stats['total_listings'] = len(df)
    stats['for_sale'] = len(df[df['transaction_type'] == 'For Sale'])
    stats['for_rent'] = len(df[df['transaction_type'] == 'For Rent'])

    # Price stats (for sale)
    sale_df = df[(df['transaction_type'] == 'For Sale') &
                 (df['price_clean'].notna()) &
                 (df['price_clean'] > 0)]

    if len(sale_df) > 0:
        stats['avg_sale_price'] = sale_df['price_clean'].mean()
        stats['median_sale_price'] = sale_df['price_clean'].median()
        stats['min_sale_price'] = sale_df['price_clean'].min()
        stats['max_sale_price'] = sale_df['price_clean'].max()

    # Price per sqm stats
    sqm_df = df[(df['price_per_sqm'].notna()) &
                (df['price_per_sqm'] > 0) &
                (df['price_per_sqm'] < 10000)]

    if len(sqm_df) > 0:
        stats['avg_price_per_sqm'] = sqm_df['price_per_sqm'].mean()
        stats['median_price_per_sqm'] = sqm_df['price_per_sqm'].median()

    # Top property type
    stats['top_property_type'] = df['property_type'].value_counts().index[0]
    stats['top_property_count'] = df['property_type'].value_counts().values[0]

    # Top district
    stats['top_district'] = df['district'].value_counts().index[0]
    stats['top_district_count'] = df['district'].value_counts().values[0]

    # Room stats
    room_df = df[df['Otaq Sayı'].notna()].copy()
    room_df['rooms'] = pd.to_numeric(room_df['Otaq Sayı'], errors='coerce')
    if len(room_df) > 0:
        stats['most_common_rooms'] = int(room_df['rooms'].mode()[0]) if len(room_df['rooms'].mode()) > 0 else None

    # Area stats
    area_df = df[(df['area_clean'].notna()) & (df['area_clean'] > 0)]
    if len(area_df) > 0:
        stats['avg_area'] = area_df['area_clean'].mean()
        stats['median_area'] = area_df['area_clean'].median()

    return stats

def main():
    """Main execution function"""
    print("=" * 70)
    print("REAL ESTATE MARKET ANALYSIS - CHART GENERATION")
    print("=" * 70)
    print()

    # Load data
    df = load_and_prepare_data()
    print()

    # Generate all charts
    print("Generating visualizations...")
    print("-" * 70)

    generate_chart_1_transaction_volume(df)
    generate_chart_2_property_type_distribution(df)
    generate_chart_3_price_distribution(df)
    generate_chart_4_average_prices(df)
    generate_chart_5_district_volume(df)
    generate_chart_6_district_prices(df)
    generate_chart_7_price_per_sqm(df)
    generate_chart_8_room_distribution(df)
    generate_chart_9_price_by_rooms(df)
    generate_chart_10_area_distribution(df)
    generate_chart_11_rental_market(df)
    generate_chart_12_price_segments(df)

    print("-" * 70)
    print()

    # Generate summary statistics
    stats = generate_summary_statistics(df)

    # Save statistics to file for README generation
    import json
    with open('market_statistics.json', 'w') as f:
        json.dump(stats, f, indent=2, default=str)

    print("=" * 70)
    print("ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"Total charts generated: 12")
    print(f"Charts saved to: {CHARTS_DIR.absolute()}")
    print(f"Statistics saved to: market_statistics.json")
    print()
    print("Key Market Statistics:")
    print(f"  • Total Listings: {stats['total_listings']:,}")
    print(f"  • For Sale: {stats['for_sale']:,}")
    print(f"  • For Rent: {stats['for_rent']:,}")
    if 'avg_sale_price' in stats:
        print(f"  • Average Sale Price: {stats['avg_sale_price']:,.0f} AZN")
    if 'avg_price_per_sqm' in stats:
        print(f"  • Average Price/m²: {stats['avg_price_per_sqm']:,.0f} AZN")
    print()

if __name__ == "__main__":
    main()
