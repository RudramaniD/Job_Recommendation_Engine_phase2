import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from geonamescache import GeonamesCache
from haversine import haversine, Unit
import pycountry

gc = GeonamesCache()
cities_dict = gc.get_cities()

CITY_LOOKUP: Dict[str, Tuple[float, float]] = {}

for city_id, city_data in cities_dict.items():
    city_name = (city_data.get("name") or "").lower()
    country_code = (city_data.get("countrycode") or "").lower()
    lat = float(city_data.get("latitude"))
    lng = float(city_data.get("longitude"))
    if city_name and country_code:
        key = f"{city_name},{country_code}"
        CITY_LOOKUP[key] = (lat, lng)

def country_to_alpha2(country: Optional[str]) -> Optional[str]:
    if not country:
        return None
    country = country.strip()
    if len(country) == 2:
        return country.lower()
    try:
        return pycountry.countries.lookup(country).alpha_2.lower()
    except LookupError:
        return None

def get_coordinates(city: str, country: str) -> Optional[Tuple[float, float]]:
    city = (city or "").strip().lower()
    country_code = country_to_alpha2(country)
    if not city or not country_code:
        return None
    key = f"{city},{country_code}"
    return CITY_LOOKUP.get(key)

def apply_filters_on_dataframe(jobs_df: pd.DataFrame, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    if jobs_df.empty or not filters:
        return jobs_df

    filtered_df = jobs_df.copy()

    def as_int_or_none(value):
        if value in (None, "", []):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    date_days_raw = filters.get("date_posted_days")
    date_days = as_int_or_none(date_days_raw)
    if date_days is not None:
        since = datetime.utcnow() - timedelta(days=date_days)
        filtered_df = filtered_df[filtered_df["activatedAt"] >= since]

    work_setting = filters.get("work_setting") or []
    if work_setting:
        filtered_df = filtered_df[
            filtered_df["jobSetting"].apply(
                lambda x: any(ws in x for ws in work_setting) if isinstance(x, list) else False
            )
        ]

    job_type = filters.get("job_type") or []
    if job_type:
        filtered_df = filtered_df[filtered_df["positionType"].isin(job_type)]

    exp_levels = filters.get("experience_levels") or []
    if exp_levels:
        filtered_df = filtered_df[filtered_df["experienceLevel"].isin(exp_levels)]

    filtered_df = apply_distance_filter(filtered_df, filters)

    return filtered_df.reset_index(drop=True)

def apply_distance_filter(jobs_df: pd.DataFrame, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    if jobs_df.empty or not filters:
        return jobs_df

    distance_km = filters.get("distance_km")
    if not distance_km:
        return jobs_df

    try:
        distance_km = float(distance_km)
    except (TypeError, ValueError):
        return jobs_df

    user_lat = filters.get("user_lat")
    user_lng = filters.get("user_lng")

    if user_lat is not None and user_lng is not None:
        try:
            user_coords = (float(user_lat), float(user_lng))
        except (TypeError, ValueError):
            user_coords = None
    else:
        user_coords = None

    if user_coords is None:
        user_city = filters.get("user_city", "")
        user_country = filters.get("user_country", "")
        user_coords = get_coordinates(user_city, user_country)

    if not user_coords:
        return jobs_df

    def job_coords_from_row(row) -> Optional[Tuple[float, float]]:
        lat = row.get("latitude")
        lng = row.get("longitude")
        if lat is not None and lng is not None:
            try:
                return float(lat), float(lng)
            except (TypeError, ValueError):
                pass
        job_city = row.get("city", "")
        job_country = row.get("country", "")
        return get_coordinates(job_city, job_country)

    def within_distance(row) -> bool:
        coords = job_coords_from_row(row)
        if not coords:
            return False
        d = haversine(user_coords, coords, unit=Unit.KILOMETERS)
        return d <= distance_km

    return jobs_df[jobs_df.apply(within_distance, axis=1)].reset_index(drop=True)
