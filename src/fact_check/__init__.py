import requests

# Define the claim to check
claim = "The earth is flat."

# Make a request to the FactCheck API
response = requests.get("https://factchecktools.googleapis.com/v1alpha1/claims:search", params={"query": claim})

# Check if the response contains any results
if response.json()["claims"]:
    # If there are results, print the verdict and explanation
    verdict = response.json()["claims"][0]["claimReview"][0]["textualRating"]
    explanation = response.json()["claims"][0]["claimReview"][0]["textualRatingExplanation"]
    print(f"The claim '{claim}' is {verdict}. {explanation}")
else:
    # If there are no results, print a message indicating that the claim could not be verified
    print(f"Could not verify the claim '{claim}'.")