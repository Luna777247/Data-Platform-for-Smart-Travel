# backend/app/api/dashboard.py
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.db.repository import PlaceRepository
from datetime import datetime, timezone

router = APIRouter()
repo = PlaceRepository()

@router.get("/overview")
async def get_overview():
    # Use MongoDB aggregation instead of loading all data
    pipeline = [
        {
            "$group": {
                "_id": None,
                "totalPlaces": {"$sum": 1},
                "avgRating": {"$avg": "$rating"},
                "minRating": {"$min": "$rating"},
                "maxRating": {"$max": "$rating"}
            }
        }
    ]
    result = await repo.collection.aggregate(pipeline).to_list(length=1)
    if result:
        data = result[0]
        return {
            "totalPlaces": data["totalPlaces"],
            "averageRating": round(data["avgRating"], 2) if data["avgRating"] else 0,
            "minRating": data["minRating"] or 0,
            "maxRating": data["maxRating"] or 0,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        }
    return {
        "totalPlaces": 0,
        "averageRating": 0,
        "minRating": 0,
        "maxRating": 0,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    }

@router.get("/places-by-category")
async def get_places_by_category():
    all_places = await repo.get_all(limit=10000)
    by_type = {}
    for p in all_places:
        t = p.get("type") or "N/A"
        by_type[t] = by_type.get(t, 0) + 1
    
    sorted_cats = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:20]
    return {
        "categories": [{"category": k, "count": v} for k, v in sorted_cats]
    }

@router.get("/places-by-rating")
async def get_places_by_rating():
    all_places = await repo.get_all(limit=10000)
    dist = {
        "4.5 - 5.0 ⭐": 0,
        "4.0 - 4.5 ⭐": 0,
        "3.0 - 4.0 ⭐": 0,
        "< 3.0 ⭐": 0
    }
    for p in all_places:
        r = p.get("rating") or 0.0
        if r >= 4.5: dist["4.5 - 5.0 ⭐"] += 1
        elif r >= 4.0: dist["4.0 - 4.5 ⭐"] += 1
        elif r >= 3.0: dist["3.0 - 4.0 ⭐"] += 1
        else: dist["< 3.0 ⭐"] += 1
    
    return {
        "ratingDistribution": [{"range": k, "count": v} for k, v in dist.items()]
    }

@router.get("/city-ranking")
async def get_city_ranking():
    # Filter junk data and use Weighted Rating logic
    all_places = await repo.get_all(limit=10000)
    filtered = [p for p in all_places if p.get("type") not in ["N/A", "test"] and p.get("city") != "unknown"]
    
    # Global Mean
    ratings = [get_rating(p) for p in filtered if get_rating(p) > 0]
    C = sum(ratings) / len(ratings) if ratings else 0
    m = 5 # min reviews threshold for weighting
    
    city_data = {}
    for p in filtered:
        city = p.get("city") or "unknown"
        if city not in city_data:
            city_data[city] = {"count": 0, "total_rating": 0, "total_reviews": 0, "categories": {}}
        
        city_data[city]["count"] += 1
        city_data[city]["total_rating"] += get_rating(p)
        city_data[city]["total_reviews"] += get_rev_count(p)
        
        # Use inferred type for ranking analysis
        cat = infer_type(p)
        city_data[city]["categories"][cat] = city_data[city]["categories"].get(cat, 0) + 1
    
    ranking = []
    for city, data in city_data.items():
        v = data["count"]
        R = data["total_rating"] / v if v > 0 else 0
        weighted_r = (v / (v + m)) * R + (m / (v + m)) * C
        
        # Find top category (excluding 'other' and 'N/A' if possible)
        meaningful_cats = {k: v for k, v in data["categories"].items() if k not in ["other", "N/A", "test"]}
        if meaningful_cats:
            top_cat = max(meaningful_cats.items(), key=lambda x: x[1])[0]
        else:
            top_cat = max(data["categories"].items(), key=lambda x: x[1])[0] if data["categories"] else "N/A"
            
        ranking.append({
            "city": str(city).capitalize(),
            "count": v,
            "avgRating": round(weighted_r, 2),
            "rawAvgRating": round(R, 2),
            "topCategory": top_cat
        })
    
    ranking.sort(key=lambda x: x["avgRating"], reverse=True)
    for idx, item in enumerate(ranking):
        item["rank"] = idx + 1
        
    return ranking[:20]

def infer_type(place: dict) -> str:
    """Helper to infer type from name if missing, for dashboard visuals."""
    t = place.get("type")
    if t and t not in ["N/A", "test", "None"]:
        return str(t).lower()
    
    name = str(place.get("name", "")).lower()
    if any(k in name for k in ["hotel", "hostel", "homestay", "nhà nghỉ", "khách sạn"]):
        return "hotel"
    if any(k in name for k in ["restaurant", "quán ăn", "nhà hàng", "phở", "bún"]):
        return "restaurant"
    if any(k in name for k in ["cafe", "cà phê", "coffee"]):
        return "cafe"
    if any(k in name for k in ["museum", "bảo tàng", "di tích"]):
        return "museum"
    if any(k in name for k in ["park", "công viên", "thác", "market", "chợ"]):
        return "attraction"
    return "other"

def get_rev_count(p: dict) -> int:
    return int(p.get("review_count") or p.get("reviews") or 0)

def get_rating(p: dict) -> float:
    r = p.get("rating")
    return float(r) if r is not None else 0.0

@router.get("/diversity-radar")
async def get_diversity_radar():
    """Returns data for Radar charts showing POI diversity of top cities."""
    all_places = await repo.get_all(limit=10000)
    
    # Infer types for all places
    for p in all_places:
        p["inferred_type"] = infer_type(p)
        
    filtered = [p for p in all_places if p["inferred_type"] != "other" and p.get("city") != "unknown"]
    
    # Let's pick top 3 cities
    city_counts = {}
    for p in filtered:
        c = p.get("city")
        city_counts[c] = city_counts.get(c, 0) + 1
    
    top_cities = sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    top_city_names = [c[0] for c in top_cities]
    
    target_cats = ["attraction", "hotel", "restaurant", "cafe", "museum"]
    
    radar_data = []
    for cat in target_cats:
        item = {"subject": cat.capitalize()}
        for city in top_city_names:
            count = sum(1 for p in filtered if p.get("city") == city and p["inferred_type"] == cat)
            share = (count / city_counts[city]) * 100 if city_counts[city] > 0 else 0
            item[city.capitalize()] = round(share, 1)
        radar_data.append(item)
    
    return {
        "cities": [c.capitalize() for c in top_city_names],
        "data": radar_data
    }

@router.get("/quality-scatter")
async def get_quality_scatter():
    """Returns data for Scatter charts (Review Count vs Rating)."""
    all_places = await repo.get_all(limit=10000)
    # Filter only those meaningful with reviews and ratings
    filtered = [p for p in all_places if get_rev_count(p) > 0 and get_rating(p) > 0]
    
    scatter_data = []
    for p in filtered[:500]: # Sample for performance
        scatter_data.append({
            "name": p.get("name"),
            "reviews": get_rev_count(p),
            "rating": get_rating(p),
            "city": (p.get("city") or "unknown").capitalize()
        })
    return scatter_data

@router.get("/data-health")
async def get_data_health():
    """Returns data health metrics (enrichment completion)."""
    all_places = await repo.get_all(limit=10000)
    total = len(all_places)
    if total == 0: return []
    
    enriched = sum(1 for p in all_places if get_rev_count(p) > 0 or get_rating(p) > 0)
    photos = sum(1 for p in all_places if p.get("photos") and len(p.get("photos")) > 0)
    basic = total - enriched
    
    return [
        {"name": "Complete (Enriched)", "value": enriched},
        {"name": "Basic (Raw)", "value": basic},
        {"name": "With Photos", "value": photos}
    ]

@router.get("/top-places")
async def get_top_places():
    all_places = await repo.get_all(limit=10000)
    # Use weighted logic: WR = (v / (v+m)) * R + (m / (v+m)) * C
    filtered = [p for p in all_places if get_rev_count(p) >= 5]
    ratings = [get_rating(p) for p in all_places if get_rating(p) > 0]
    C = sum(ratings) / len(ratings) if ratings else 0
    m = 10
    
    for p in filtered:
        v = get_rev_count(p)
        R = get_rating(p)
        p["score"] = (v / (v + m)) * R + (m / (v + m)) * C
        
    sorted_places = sorted(filtered, key=lambda x: x.get("score", 0), reverse=True)
    top = []
    for p in sorted_places[:12]:
        top.append({
            "id": str(p.get("_id", p.get("u_key"))),
            "name": p.get("name"),
            "category": p.get("type") or "N/A",
            "rating": p.get("rating") or 0.0,
            "reviewCount": p.get("review_count") or 0,
            "city": p.get("city").capitalize()
        })
    return {"topPlaces": top}

@router.get("/places-by-province")
async def get_places_by_province():
    all_places = await repo.get_all(limit=10000)
    by_city = {}
    for p in all_places:
        c = p.get("city") or "unknown"
        by_city[c] = by_city.get(c, 0) + 1
        
    sorted_provinces = sorted(by_city.items(), key=lambda x: x[1], reverse=True)[:20]
    return {
        "provinces": [{"province": k.capitalize(), "count": v} for k, v in sorted_provinces]
    }

@router.get("/average-rating-by-category")
async def get_avg_rating_by_category():
    all_places = await repo.get_all(limit=10000)
    cat_data = {}
    for p in all_places:
        cat = p.get("type") or "N/A"
        if cat not in cat_data:
            cat_data[cat] = {"count": 0, "total_rating": 0}
        cat_data[cat]["count"] += 1
        cat_data[cat]["total_rating"] += p.get("rating") or 0.0
    
    cat_ratings = []
    for cat, data in cat_data.items():
        avg_r = data["total_rating"] / data["count"] if data["count"] > 0 else 0
        cat_ratings.append({
            "category": cat,
            "avgRating": round(avg_r, 2)
        })
    
    cat_ratings.sort(key=lambda x: x["avgRating"], reverse=True)
    return {"categoryRatings": cat_ratings[:20]}

@router.get("/city-category-matrix")
async def get_city_category_matrix():
    all_places = await repo.get_all(limit=10000)
    cities_count = {}
    cats_count = {}
    matrix_data = {}
    
    all_places = await repo.get_all(limit=10000)
    cities_count = {}
    cats_count = {}
    matrix_data = {}
    
    for p in all_places:
        city = str(p.get("city") or "unknown").capitalize()
        # Use inferred type for heatmap matrix
        cat = infer_type(p).capitalize()
        
        cities_count[city] = cities_count.get(city, 0) + 1
        cats_count[cat] = cats_count.get(cat, 0) + 1
        matrix_data[(city, cat)] = matrix_data.get((city, cat), 0) + 1
        
    # Predefined top cities if possible, or just the top contributors
    top_cities = sorted(cities_count.keys(), key=lambda x: cities_count[x], reverse=True)[:10]
    # Filter out 'Other' from top categories if desired
    ordered_cats = sorted(cats_count.keys(), key=lambda x: cats_count[x], reverse=True)
    top_cats = [c for c in ordered_cats if c != "Other"][:8]
    
    matrix = []
    max_val = 0
    for city in top_cities:
        row = []
        for cat in top_cats:
            val = matrix_data.get((city, cat), 0)
            row.append(val)
            if val > max_val: max_val = val
        matrix.append(row)
        
    return {
        "cities": top_cities,
        "categories": top_cats,
        "matrix": matrix,
        "maxValue": max_val
    }


@router.get("/map-data")
async def get_map_data():
    all_places = await repo.get_all(limit=10000)
    map_points = []
    for p in all_places:
        loc = p.get("location", {})
        coords = loc.get("coordinates")
        if coords and len(coords) == 2:
            # coords is [lon, lat] in mongo format usually
            map_points.append({
                "lat": coords[1],
                "lon": coords[0],
                "name": p.get("name"),
                "category": p.get("type"),
                "rating": p.get("rating", 0),
                "reviewCount": p.get("review_count", 0)
            })
    
    return {"mapData": map_points}
