import requests
import json
# import related models here
from .models import CarDealer, DealerReview
from requests.auth import HTTPBasicAuth
from django.http import JsonResponse

# Create a `get_request` to make HTTP GET requests
# e.g., response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
#                                     auth=HTTPBasicAuth('apikey', api_key))
def get_request(url, **kwargs):
    print(kwargs)
    print("GET from {} ".format(url))
    try:
        # Call get method of requests library with URL and parameters
        response = requests.get(url, headers={'Content-Type': 'application/json'},
                                    params=kwargs)
    except:
        # If any error occurs
        print("Network exception occurred")
    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data

# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)


# Create a get_dealers_from_cf method to get dealers from a cloud function
# def get_dealers_from_cf(url, **kwargs):
# - Call get_request() with specified arguments
# - Parse JSON results into a CarDealer object list
def get_dealers_from_cf(url, **kwargs):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url)
    if json_result:
        # Get the row list in JSON as dealers
        dealers = json_result["dbs"]
        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            dealer_doc = dealer["doc"]
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"],
                                   id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                                   short_name=dealer_doc["short_name"],
                                   st=dealer_doc["st"], zip=dealer_doc["zip"])
            results.append(dealer_obj)
  
    return results



# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
# def get_dealer_by_id_from_cf(url, dealerId):
# - Call get_request() with specified arguments
# - Parse JSON results into a DealerView object list

def get_dealer_reviews_from_cf(dealership):
    url = "https://us-east.functions.appdomain.cloud/api/v1/web/befaae8a-3d64-42a4-9aab-bdbd5aa2dd89/reviews-package/fucking%20tired%202"  # Replace with your actual cloud function URL
    response = requests.get(url, params={'dealership': dealership})
    
    dealer_reviews = []
    if response.status_code == 200:
        data = response.json()
        reviews_data = data.get('reviews', [])
        for review_data in reviews_data:
            review = DealerReview(
                dealership=review_data.get("dealership", ""),
                name=review_data.get("name", ""),
                purchase=review_data.get("purchase", ""),
                review=review_data.get("review", ""),
                purchase_date=review_data.get("purchase_date", ""),
                car_make=review_data.get("car_make", ""),
                car_model=review_data.get("car_model", ""),
                car_year=review_data.get("car_year", ""),
                sentiment=review_data.get("sentiment", ""),  # You need to define analyze_review_sentiments function
                id=review_data.get("id", "")
            )
            dealer_reviews.append(review)
    
    return dealer_reviews

def get_dealer_by_id_from_cf(id):
    results = []
    url = "https://us-east.functions.appdomain.cloud/api/v1/web/befaae8a-3d64-42a4-9aab-bdbd5aa2dd89/dealership-package/get_specific_dealer"
    # Call get_request with a URL parameter
    response = requests.get(url, params={'id': id})
    if response.status_code == 200:
        data = response.json()
        dealers = data.get('dbs', [])  # Assuming 'dbs' contains the list of dealers
        
        # Iterate through each dealer dictionary
        for dealer_details in dealers:
            # Create a CarDealer object with values from the dealer_details dictionary
            dealer_obj = CarDealer(
                address=dealer_details["address"],
                city=dealer_details["city"],
                full_name=dealer_details["full_name"],
                id=dealer_details["id"],
                lat=dealer_details["lat"],
                long=dealer_details["long"],
                short_name=dealer_details["short_name"],
                st=dealer_details["st"],
                zip=dealer_details["zip"]
            )
            
            results.append(dealer_obj)
  
    return results



# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
# def analyze_review_sentiments(text):
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative
def add_review(request, dealer_id):
    if request.method == "GET":
        url = f"https://service.eu.apiconnect.ibmcloud.com/gws/apigateway/api/a9220b6d6b26f1eb3b657a98770b743616f7d4cd223b89cd1ca4e88ab49bdb92/api/dealership?dealerId={dealer_id}"
        # Get dealers from the URL
        context = {
            "cars": CarModel.objects.all(),
            "dealer": get_dealers_from_cf(url)[0],
        }
        print(context)
        return render(request, 'djangoapp/add_review.html', context)
    if request.method == "POST":
        form = request.POST
        review = {
            "name": f"{request.user.first_name} {request.user.last_name}",
            "dealership": dealer_id,
            "review": form["content"],
            "purchase": form.get("purchasecheck"),
            }
        if form.get("purchasecheck"):
            review["purchasedate"] = datetime.strptime(form.get("purchasedate"), "%m/%d/%Y").isoformat()
            car = CarModel.objects.get(pk=form["car"])
            review["car_make"] = car.car_make.name
            review["car_model"] = car.name
            review["car_year"]= car.year.strftime("%Y")
        json_payload = {"review": review}
        URL = 'https://service.eu.apiconnect.ibmcloud.com/gws/apigateway/api/a9220b6d6b26f1eb3b657a98770b743616f7d4cd223b89cd1ca4e88ab49bdb92/api/review'
        post_request(URL, json_payload, dealerId=dealer_id)
    return redirect("djangoapp:dealer_details", dealer_id=dealer_id)


