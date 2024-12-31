import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json

matplotlib.use('Agg')  # Use non-GUI backend

def flattenDF(reviews_data):
    flattened_data = []
    #for flattening the data of reviews to allow it to be stored in a data frame
    for review in reviews_data:
        for key, details in review.items():
            #splitting review number
            review_number = int(key.split("_")[-1])
            #unpacking ratings dict into three values in 1 dict
            ratings = {rating_type: int(value) for rating in details["Ratings"] for rating_type, value in rating.items()}
            #appending it to the data
            flattened_data.append({
                "review_count": review_number,
                "overall": ratings.get("Overall", None),
                "food": ratings.get("Food", None),
                "service": ratings.get("Service", None),
                "ambience": ratings.get("Ambience", None),
                "date": details["Date"],
                "review": details["Review"]
            })

    return flattened_data

def preprocess_date(date_str):
    #if it is dined today 
    if "Dined today" in date_str:
        return "2024-01-01"  #replace with a hard coded string
    elif "Dined " in date_str and "days ago" in date_str:
        #extract number of days and subtract it from 2024-01-01
        days_ago = int(date_str.split(" ")[1])
        calculated_date = datetime(2024, 1, 1) - timedelta(days=days_ago)
        return calculated_date.strftime("%Y-%m-%d")
    else:
        #remove Dined on from string
        cleaned_date = date_str.replace("Dined on ", "")
        try:
            #convert date time into natural time (2024-01-01 00:00:00)
            parsed_date = datetime.strptime(cleaned_date, "%B %d, %Y")
            #change its shape to 2024-01-01
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            #return as it is if parsing fails
            return cleaned_date


def visualizeData(competitor_reviews):
    #flatten competitor reviews
    competitor_reviews = flattenDF(competitor_reviews)
    with open("reviews.json","r") as f:
        my_reviews = json.load(f)
    #flatten reviews of my picked restaurant
    my_reviews = flattenDF(my_reviews)

    df_my = pd.DataFrame(my_reviews)
    df_comp = pd.DataFrame(competitor_reviews)
    #standardize dates as datetime objects of pandas
    for df in [df_my, df_comp]:
        df["date"] = pd.to_datetime(df["date"].astype(str).apply(preprocess_date))

    #group by years and get mean of overall,food and service rating, also getting size of overall reviews for popularit
    popularity_my = df_my.groupby(df_my["date"].dt.to_period("Y")).agg(
        review_count=("overall", "size"),
        avg_overall=("overall", "mean"),
        avg_food=("food", "mean"),
        avg_service=("service", "mean"),
    ).reset_index()
    #doing the same for competitor
    popularity_comp = df_comp.groupby(df_comp["date"].dt.to_period("Y")).agg(
        review_count=("overall", "size"),
        avg_overall=("overall", "mean"),
        avg_food=("food", "mean"),
        avg_service=("service", "mean"),
    ).reset_index()

    #convert years back to time stamps
    popularity_my["date"] = popularity_my["date"].dt.to_timestamp()
    popularity_comp["date"] = popularity_comp["date"].dt.to_timestamp()

    #create plot using subplots
    plt.figure(figsize=(18, 12))

    plt.subplot(3, 1, 1)
    plt.plot(popularity_my["date"], popularity_my["avg_overall"], marker="o", linestyle="-", color="blue", label="My Restaurant")
    plt.plot(popularity_comp["date"], popularity_comp["avg_overall"], marker="o", linestyle="-", color="red", label="Competitor Restaurant")
    plt.title("Average Overall Ratings Per Year", fontsize=16)
    plt.xlabel("Date", fontsize=14)
    plt.ylabel("Average Overall Rating", fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(visible=True, linestyle="--", alpha=0.7)

    plt.subplot(3, 1, 2)
    plt.plot(popularity_my["date"], popularity_my["avg_food"], marker="o", linestyle="-", color="blue", label="My Restaurant")
    plt.plot(popularity_comp["date"], popularity_comp["avg_food"], marker="o", linestyle="-", color="red", label="Competitor Restaurant")
    plt.title("Average Food Ratings Per Year", fontsize=16)
    plt.xlabel("Date", fontsize=14)
    plt.ylabel("Average Food Rating", fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(visible=True, linestyle="--", alpha=0.7)

    plt.subplot(3, 1, 3)
    plt.plot(popularity_my["date"], popularity_my["avg_service"], marker="o", linestyle="-", color="blue", label="My Restaurant")
    plt.plot(popularity_comp["date"], popularity_comp["avg_service"], marker="o", linestyle="-", color="red", label="Competitor Restaurant")
    plt.title("Average Service Ratings Per Year", fontsize=16)
    plt.xlabel("Date", fontsize=14)
    plt.ylabel("Average Service Rating", fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(visible=True, linestyle="--", alpha=0.7)

    plt.tight_layout()
    plt.savefig("static/images/ratings_comparison_yearly.png")
    plt.close()
    return

