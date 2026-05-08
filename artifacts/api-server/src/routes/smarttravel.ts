import { Router } from "express";

const router = Router();

const cities = ["hanoi", "hcmc", "danang", "hue", "hoian", "nhatrang", "dalat", "quangnam"];
const categories = ["restaurant", "hotel", "cafe", "attraction", "museum", "park", "beach", "bar"];

function rng(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function buildSamplePlaces() {
  const places: Array<{
    id: string; name: string; city: string; type: string;
    rating: number; reviewCount: number; lat: number; lon: number;
  }> = [];
  const cityCoords: Record<string, [number, number]> = {
    hanoi: [21.03, 105.85], hcmc: [10.78, 106.7], danang: [16.06, 108.22],
    hue: [16.46, 107.6], hoian: [15.88, 108.33], nhatrang: [12.24, 109.19],
    dalat: [11.94, 108.44], quangnam: [15.57, 108.47]
  };
  const names: Record<string, string[]> = {
    restaurant: ["Pho 24", "Bun Cha Ha Noi", "Banh Mi Phuong", "Nem Nuong Ninh Hoa", "Com Tam Saigon"],
    hotel: ["Metropole Hotel", "Park Hyatt", "Sofitel Legend", "Fusion Maia", "Anantara Hoi An"],
    cafe: ["Cafe Giang", "The Workshop", "Cong Caphe", "Highlands Coffee", "Ca Phe Trung"],
    attraction: ["Hoan Kiem Lake", "Ben Thanh Market", "My Son Sanctuary", "Hue Citadel", "Da Lat Palace"],
    museum: ["Vietnam Museum", "War Remnants Museum", "Cham Museum", "Fine Arts Museum"],
    park: ["Reunification Palace", "Thu Le Park", "Ba Na Hills"],
    beach: ["My Khe Beach", "Lang Co Beach", "Nha Trang Beach"],
    bar: ["Skybar", "Bui Vien Street", "Ta Hien Street"]
  };

  let idx = 0;
  for (const city of cities) {
    const [baseLat, baseLon] = cityCoords[city];
    const count = 30 + Math.floor(rng(idx++) * 50);
    for (let i = 0; i < count; i++) {
      const cat = categories[Math.floor(rng(idx++) * categories.length)];
      const nameList = names[cat] || names.restaurant;
      const name = nameList[Math.floor(rng(idx++) * nameList.length)] + ` (${city.charAt(0).toUpperCase() + city.slice(1)} ${i + 1})`;
      const rating = Math.round((3.0 + rng(idx++) * 2.0) * 10) / 10;
      const reviewCount = Math.floor(rng(idx++) * 2000) + 10;
      places.push({
        id: `place-${city}-${i}`,
        name,
        city,
        type: cat,
        rating,
        reviewCount,
        lat: baseLat + (rng(idx++) - 0.5) * 0.2,
        lon: baseLon + (rng(idx++) - 0.5) * 0.2
      });
    }
  }
  return places;
}

const samplePlaces = buildSamplePlaces();

router.get("/smart-travel/dashboard/overview", (_req, res) => {
  const ratings = samplePlaces.map(p => p.rating).filter(r => r > 0);
  const avgRating = ratings.reduce((a, b) => a + b, 0) / ratings.length;
  res.json({
    totalPlaces: samplePlaces.length,
    averageRating: Math.round(avgRating * 100) / 100,
    minRating: Math.min(...ratings),
    maxRating: Math.max(...ratings),
    timestamp: new Date().toISOString()
  });
});

router.get("/smart-travel/dashboard/places-by-category", (_req, res) => {
  const byCat: Record<string, number> = {};
  for (const p of samplePlaces) {
    byCat[p.type] = (byCat[p.type] || 0) + 1;
  }
  const categories = Object.entries(byCat)
    .sort((a, b) => b[1] - a[1])
    .map(([category, count]) => ({ category, count }));
  res.json({ categories });
});

router.get("/smart-travel/dashboard/places-by-rating", (_req, res) => {
  const dist: Record<string, number> = {
    "4.5 - 5.0 ⭐": 0, "4.0 - 4.5 ⭐": 0, "3.0 - 4.0 ⭐": 0, "< 3.0 ⭐": 0
  };
  for (const p of samplePlaces) {
    if (p.rating >= 4.5) dist["4.5 - 5.0 ⭐"]++;
    else if (p.rating >= 4.0) dist["4.0 - 4.5 ⭐"]++;
    else if (p.rating >= 3.0) dist["3.0 - 4.0 ⭐"]++;
    else dist["< 3.0 ⭐"]++;
  }
  res.json({
    ratingDistribution: Object.entries(dist).map(([range, count]) => ({ range, count }))
  });
});

router.get("/smart-travel/dashboard/city-ranking", (_req, res) => {
  const cityData: Record<string, { count: number; totalRating: number; cats: Record<string, number> }> = {};
  for (const p of samplePlaces) {
    if (!cityData[p.city]) cityData[p.city] = { count: 0, totalRating: 0, cats: {} };
    cityData[p.city].count++;
    cityData[p.city].totalRating += p.rating;
    cityData[p.city].cats[p.type] = (cityData[p.city].cats[p.type] || 0) + 1;
  }
  const allRatings = samplePlaces.map(p => p.rating);
  const C = allRatings.reduce((a, b) => a + b, 0) / allRatings.length;
  const m = 5;
  const ranking = Object.entries(cityData).map(([city, data], idx) => {
    const v = data.count;
    const R = data.totalRating / v;
    const weightedR = (v / (v + m)) * R + (m / (v + m)) * C;
    const topCat = Object.entries(data.cats).sort((a, b) => b[1] - a[1])[0]?.[0] || "N/A";
    return { city: city.charAt(0).toUpperCase() + city.slice(1), count: v, avgRating: Math.round(weightedR * 100) / 100, rawAvgRating: Math.round(R * 100) / 100, topCategory: topCat, rank: idx + 1 };
  }).sort((a, b) => b.avgRating - a.avgRating).map((item, i) => ({ ...item, rank: i + 1 }));
  res.json(ranking);
});

router.get("/smart-travel/dashboard/top-places", (_req, res) => {
  const allRatings = samplePlaces.map(p => p.rating);
  const C = allRatings.reduce((a, b) => a + b, 0) / allRatings.length;
  const m = 10;
  const scored = samplePlaces
    .filter(p => p.reviewCount >= 5)
    .map(p => ({ ...p, score: (p.reviewCount / (p.reviewCount + m)) * p.rating + (m / (p.reviewCount + m)) * C }))
    .sort((a, b) => b.score - a.score)
    .slice(0, 12)
    .map(p => ({
      id: p.id,
      name: p.name,
      category: p.type,
      rating: p.rating,
      reviewCount: p.reviewCount,
      city: p.city.charAt(0).toUpperCase() + p.city.slice(1)
    }));
  res.json({ topPlaces: scored });
});

router.get("/smart-travel/dashboard/places-by-province", (_req, res) => {
  const byCity: Record<string, number> = {};
  for (const p of samplePlaces) {
    byCity[p.city] = (byCity[p.city] || 0) + 1;
  }
  const provinces = Object.entries(byCity)
    .sort((a, b) => b[1] - a[1])
    .map(([province, count]) => ({ province: province.charAt(0).toUpperCase() + province.slice(1), count }));
  res.json({ provinces });
});

router.get("/smart-travel/dashboard/average-rating-by-category", (_req, res) => {
  const catData: Record<string, { total: number; count: number }> = {};
  for (const p of samplePlaces) {
    if (!catData[p.type]) catData[p.type] = { total: 0, count: 0 };
    catData[p.type].total += p.rating;
    catData[p.type].count++;
  }
  const categoryRatings = Object.entries(catData)
    .map(([category, d]) => ({ category, avgRating: Math.round((d.total / d.count) * 100) / 100 }))
    .sort((a, b) => b.avgRating - a.avgRating);
  res.json({ categoryRatings });
});

router.get("/smart-travel/dashboard/city-category-matrix", (_req, res) => {
  const cityList = cities.map(c => c.charAt(0).toUpperCase() + c.slice(1));
  const catList = categories.map(c => c.charAt(0).toUpperCase() + c.slice(1));
  const matrix = cityList.map(city => catList.map(cat =>
    samplePlaces.filter(p =>
      p.city.toLowerCase() === city.toLowerCase() &&
      p.type.toLowerCase() === cat.toLowerCase()
    ).length
  ));
  const maxValue = Math.max(...matrix.flat());
  res.json({ cities: cityList, categories: catList, matrix, maxValue });
});

router.get("/smart-travel/dashboard/map-data", (_req, res) => {
  const mapData = samplePlaces.map(p => ({
    lat: p.lat,
    lon: p.lon,
    name: p.name,
    category: p.type,
    rating: p.rating,
    reviewCount: p.reviewCount
  }));
  res.json({ mapData });
});

router.get("/smart-travel/dashboard/diversity-radar", (_req, res) => {
  const targetCats = ["attraction", "hotel", "restaurant", "cafe", "museum"];
  const cityData: Record<string, Record<string, number>> = {};
  const cityTotals: Record<string, number> = {};
  for (const p of samplePlaces) {
    if (!cityData[p.city]) cityData[p.city] = {};
    cityData[p.city][p.type] = (cityData[p.city][p.type] || 0) + 1;
    cityTotals[p.city] = (cityTotals[p.city] || 0) + 1;
  }
  const topCities = Object.entries(cityTotals).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([c]) => c);
  const data = targetCats.map(cat => {
    const item: Record<string, string | number> = { subject: cat.charAt(0).toUpperCase() + cat.slice(1) };
    for (const city of topCities) {
      const count = cityData[city]?.[cat] || 0;
      const share = cityTotals[city] > 0 ? Math.round((count / cityTotals[city]) * 1000) / 10 : 0;
      item[city.charAt(0).toUpperCase() + city.slice(1)] = share;
    }
    return item;
  });
  res.json({ cities: topCities.map(c => c.charAt(0).toUpperCase() + c.slice(1)), data });
});

export default router;
