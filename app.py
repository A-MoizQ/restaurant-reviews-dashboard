from flask import Flask, render_template, request,url_for
import time
from scrapper import scrapeRestaurant
from visualizer import visualizeData
import json

app = Flask(__name__)

with open("reviews.json", "r") as f:
    original_reviews = json.load(f)

with open("analysis.json", "r") as f:
    extracted_comments = json.load(f)

#had to map reviews to comments for display 
def merge_reviews_and_comments(original_reviews, extracted_comments):
    merged_reviews = []
    #a dictionary based on review number, used later for looking up reviews
    comment_lookup = {
        comment["Review"]: comment for comment in extracted_comments
    }
    
    for review in original_reviews:
        for key, review_data in review.items():
            #extract review number from original review
            try:
                review_number = int(key.split("_")[-1])
            except ValueError:
                continue  #skip if review gives error
            
            #find the matching comment based on review number
            matching_comment = comment_lookup.get(review_number)
            
            if matching_comment:
                #simply add direct html css to the matching comment for highlighting
                review_data["HighlightedFood"] = (
                    f"<span style='background-color: yellow;'>{matching_comment['Comment about food']}</span>"
                    if matching_comment["Comment about food"] != "no information given" else "No comments about food."
                )
                review_data["HighlightedService"] = (
                    f"<span style='background-color: lightblue;'>{matching_comment['Comment about staff/service']}</span>"
                    if matching_comment["Comment about staff/service"] != "no information given" else "No comments about staff/service."
                )
            else:
                #if no matching comment found then just write no comment
                review_data["HighlightedFood"] = "No comments about food."
                review_data["HighlightedService"] = "No comments about staff/service."
            
            #append the reviews into merged_reviews
            merged_reviews.append(review_data)
    
    return merged_reviews

#get merged data from reviews and comments
merged_reviews = merge_reviews_and_comments(original_reviews, extracted_comments)


@app.route("/")
def reviews():
    #sets up a search query
    query = request.args.get("query", "").lower()
    search_type = request.args.get("type", "all")  #three types of search: 'all', 'food', and 'staff/service'
    #get first page number
    page = int(request.args.get("page", 1))
    #setting number of reviews per page
    per_page = 10

    #only displaying reviews based on search_type
    filtered_reviews = []
    for review in merged_reviews:
        include_review = False

        #if search type is all or food
        if search_type in ["all", "food"]:
            #if it has comment about food
            if "No comments about food" not in review["HighlightedFood"]:
                if query in review["HighlightedFood"].lower() or not query:
                    #highlight ther review
                    review["HighlightedFood"] = (
                        f"<span style='background-color: yellow;'>{review['HighlightedFood']}</span>"
                        if query in review["HighlightedFood"].lower()
                        else review["HighlightedFood"]
                    )
                    include_review = True

        #if search_type is all or service
        if search_type in ["all", "service"]:
            #if it has comments about service/staff
            if "No comments about staff/service" not in review["HighlightedService"]:
                if query in review["HighlightedService"].lower() or not query:
                    #highlight review
                    review["HighlightedService"] = (
                        f"<span style='background-color: lightblue;'>{review['HighlightedService']}</span>"
                        if query in review["HighlightedService"].lower()
                        else review["HighlightedService"]
                    )
                    include_review = True
        #append reviews into the filtered_reviews
        if include_review:
            filtered_reviews.append(review)

    #get total number of reviews
    total_reviews = len(filtered_reviews)
    #calculate total number of pages based on filtered reviews length and reviews per page
    total_pages = (total_reviews + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    #get the reviews to be shown in the current page
    paginated_reviews = filtered_reviews[start:end]

    #logic to show two pages behind and 2 pages forward in the pagination bar
    start_range = max(1, page - 2)
    end_range = min(total_pages, page + 2)
    pagination_range = list(range(start_range, end_range + 1))

    #logic to include first three and last three pages no matter where the user is
    if 1 not in pagination_range:
        pagination_range.insert(0, 1)
        if 2 not in pagination_range:
            pagination_range.insert(1, 2)
    if total_pages not in pagination_range:
        if total_pages - 1 not in pagination_range:
            pagination_range.append(total_pages - 1)
        pagination_range.append(total_pages)
    
    #render template with processed data
    return render_template(
        "index.html",
        reviews=paginated_reviews,
        current_page=page,
        total_pages=total_pages,
        pagination_range=pagination_range,
        query=query,
        search_type=search_type,
    )


@app.route("/analysis")
def analysis():
    plots = [
        {"title": "Overall Rating Distribution", "filename": "overall_rating_distribution.png"},
        {"title": "Popularity Over The Years", "filename": "popularity_over_time_yearly.png"},
        {"title": "Food Rating Distribution", "filename": "food_rating_distribution.png"},
        {"title": "Service Rating Distribution", "filename": "service_rating_distribution.png"},
        {"title": "Sentiment Distribution", "filename": "sentiment_distribution_bar.png"}  
    ]
    return render_template("analysis.html",plots = plots)

@app.route("/comparison")
def comparison():
    return render_template("comparison.html")

@app.route("/compare", methods=["POST"])
def compare():
    competitor_url = request.form.get("competitor_url")

    #scrape competitor restaurant reviews
    competitor_reviews = scrapeRestaurant(competitor_url)

    #visualize and save graph
    visualizeData(competitor_reviews)

    #append current time to make url different so that new image is loaded
    graph_url = url_for('static', filename='images/ratings_comparison_yearly.png') + f"?{time.time()}"

    #render the template
    return render_template("comparison.html", graph_url=graph_url)

if __name__ == "__main__":
    app.run(debug=True)
