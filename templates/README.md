# TEXT TO POT

TEXT TO POT is a simple African recipe recommender: enter pantry ingredients, call OpenAI to generate 3 authentic African recipes, and save them to MySQL for display as clickable recipe cards.

## Features
- Clean, responsive UI
- Flask backend that calls OpenAI and saves results to MySQL
- Saves up to 3 recipes per suggestion
- Easy to deploy (Bolt.new guidance below)
- Monetization notes for IntaSend included

## Local setup (development)

1. Create virtual env and install:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
