from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
# from .models import related models
from .models import CarDealer, CarModel, CarMake, DealerReview
# from .restapis import related methods
from .restapis import get_dealers_from_cf, get_dealer_reviews_from_cf, get_request, get_dealer_by_id_from_cf
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json, requests

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.
def index(request):
    return render(request, 'djangoapp/index.html', context)

# Create an `about` view to render a static about page
# def about(request):
# ...
def about(request):
    return render(request, 'djangoapp/about.html')

# Create a `contact` view to return a static contact page
#def contact(request):
def contact(request):
    return render(request, 'djangoapp/contact.html')
    
# Create a `login_request` view to handle sign in request
# def login_request(request):
# ...
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'djangoapp/login.html', context)
    else:
        return render(request, 'djangoapp/login.html', context)

# Create a `logout_request` view to handle sign out request
# def logout_request(request):
# ...
def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
# def registration_request(request):
# ...
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            context['message'] = "That user already exists."
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        context = {}
        url = "https://us-east.functions.appdomain.cloud/api/v1/web/befaae8a-3d64-42a4-9aab-bdbd5aa2dd89/dealership-package/get-dealerships"
        dealerships = get_dealers_from_cf(url)
        context["dealership_list"] = dealerships
        return render(request, 'djangoapp/index.html', context)

# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
# ...
def get_dealer_details(request, dealer_id):
    if request.method == "GET":
        context = {}
        # id == dealer_id
        # url = "https://us-east.functions.appdomain.cloud/api/v1/web/befaae8a-3d64-42a4-9aab-bdbd5aa2dd89/reviews-package/fucking%20tired%202"
        # Call the get_dealer_reviews_from_cf function to get reviews
        reviews = get_dealer_reviews_from_cf(dealer_id)
        context["reviews"] = reviews
        print("Review object:", reviews)
        dealer = get_dealer_by_id_from_cf(dealer_id)
        print("Dealer object:", dealer)
        context["dealer"] = dealer
        

        # Now you can add any additional logic to fetch dealership details
        # For example, if you have a function to get dealer details, you can call it
        # dealer = get_dealer_details_function(dealer_id)
        # context["dealer"] = dealer

        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# ...

def post_request(url, data, headers=None):
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"POST request failed: {e}")
        return None

def add_review(request, dealer_id):
    if request.method == "GET":
        # Use the get_dealer_by_id_from_cf function to fetch dealer details
        dealer = get_dealer_by_id_from_cf(dealer_id)
        context = {
            "cars": CarModel.objects.all(),
            "dealer": dealer,
            "dealer_id": dealer_id,
            "user": request.user  # Pass the user object
        }
        return render(request, 'djangoapp/add_review.html', context)
    
    if request.method == "POST":
        # Check if the user is authenticated (logged in)
        if request.user.is_authenticated:
            # Handle the review submission here
            form = request.POST
            purchasecheck = "true" if "purchasecheck" in form else "false"
            review = {
                "name": f"{request.user.first_name} {request.user.last_name}",
                "dealership": dealer_id,
                "review": form["content"],
                "purchase": form.get("purchasecheck"),
            }
            
            if form.get("purchasecheck"):
                review["purchase_date"] = datetime.strptime(form.get("purchasedate"), "%m/%d/%Y").strftime("%m/%d/%Y")
                car = CarModel.objects.get(pk=form["car"])
                review["car_make"] = car.make.name
                review["car_model"] = car.name
                review["car_year"] = car.year.strftime("%Y")
            
            json_payload = {"review": review}
            URL = 'https://us-east.functions.appdomain.cloud/api/v1/web/befaae8a-3d64-42a4-9aab-bdbd5aa2dd89/reviews-package/post-review'
            post_request(URL, json_payload)
            
            # Redirect to the dealer details page after review submission
            return redirect("djangoapp:dealer_details", dealer_id=dealer_id)
        else:
            # Redirect unauthenticated user to the index page
            return redirect("djangoapp:index")