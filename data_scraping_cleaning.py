# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 08:55:08 2020

@author: Kremena Ivanov
"""
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import time
import re

headers = {'User-Agent': 'Brave'}

# In[]
'''DATA SCRAPING'''

'''Scraping recipe links'''
base_link = 'https://www.allrecipes.com/recipes/187/holidays-and-events/christmas/?page='
scrape_links = [base_link+str(i) for i in range(1,41)]

links = []
recipes_names = []

for url in scrape_links:
    print("Processing {}...".format(url))
    recipes = requests.get(url, headers=headers)
    recipes = BeautifulSoup(recipes.text, 'html.parser')
    if url[-2:]== '=1':
        recipes_links = recipes.select(".card__detailsContainer-left a")
    else:
        recipes_links = recipes.select(".tout__contentHeadline a")
    
    for link in recipes_links:
        if '/recipe/' in link['href']:
            links.append(link['href'])
            recipes_names.append(link['title'].strip())
    time.sleep(1)

links_full = []
for link in links:
    if link.startswith('/recipe/'):
        url = 'https://www.allrecipes.com'+str(link)
    else:
        url = link
    links_full.append(url)

recipes_id = []
for link in links_full:
    rID = link.replace('https://www.allrecipes.com/recipe/','')
    rID = rID[:rID.find('/')]
    recipes_id.append(rID)
    

df_recipes = pd.DataFrame(list(zip(links_full,recipes_id,recipes_names)))
df_recipes.columns = ['url','id','name']
# drop duplicates if any
df_recipes = df_recipes.drop_duplicates()
df_recipes.index = df_recipes['id']
df_recipes = df_recipes.drop(['id'], axis=1)
df_recipes['url'] = df_recipes['url'].str[:-1].str.rsplit('/',1).str.get(0)

'''Scraping recipe info'''
recipeIDs = list(df_recipes.index)

dic_ratings = {}
dic_stars = {}
dic_nutrition = {}
dic_category = {}
dic_time_info = {}
dic_reviews_photos = {}

for rID in recipeIDs:
    #recipe link
    link = 'https://www.allrecipes.com/recipe/'+str(rID)
    print("Processing... {}".format(link))

    recipe = requests.get(link, headers=headers)
    recipe.raise_for_status()
    soup = BeautifulSoup(recipe.text, 'html.parser')
    
    ratings = soup.select('.ugc-ratings-item')  
    rp = soup.select('.partial.ugc-ratings a')
    reviews_photos = [i.text.strip()+';' for i in rp]
    stars = soup.select('.review-star-text')
    nutrition = soup.select('.recipe-nutrition-section .section-body')
    ti = soup.select('.recipe-meta-item-body')
    time_info = [i.text.strip()+';' for i in ti]
    cat = soup.select('.breadcrumbs__title')
    categories = [i.text.strip()+'>' for i in cat[2:]]
    
    dic_ratings[rID] = ratings[0].text.strip()
    dic_stars[rID] = stars[0].text.strip()
    if len(nutrition) > 0:
        dic_nutrition[rID] = nutrition[0].text.strip()
    else:
        dic_nutrition[rID] = ''
    dic_category[rID] = ''.join(categories)[:-1]   
    dic_time_info[rID] = ''.join(time_info)[:-1]
    dic_reviews_photos[rID] = ''.join(reviews_photos)[:-1]
    time.sleep(1)

df_recipe_info = pd.DataFrame.from_dict([dic_category,
                                         dic_ratings,
                                         dic_reviews_photos,
                                         dic_stars,
                                         dic_nutrition,
                                         dic_time_info], orient='columns')
df_recipe_info = df_recipe_info.T
df_recipe_info.columns = ['category', 'ratings','reviews_photos',
                          'stars','nutrition','time_info']
df_recipe_info.index.name = 'id'

# In[]

'''DATA CLEANING'''
recipes = pd.merge(df_recipes, df_recipe_info, left_index=True, right_index=True)

'''FORMATING reviews_photos'''
recipes['reviews'] = recipes['reviews_photos'].str.split(';').str.get(0)
recipes['photos'] = recipes['reviews_photos'].str.split(';').str.get(1)
recipes['reviews'] = recipes['reviews'].str.split().str.get(0).str.replace(',','')
recipes['photos'] = recipes['photos'].str.split().str.get(0).str.replace(',','')
recipes['photos'][recipes['photos'].isnull()] = 0
recipes['reviews'] = recipes['reviews'].astype('int')
recipes['photos'] = recipes['photos'].astype('int')

'''FORMATING time_info'''
# recipes with ADD TIME
fltr = recipes['time_info'][recipes['time_info'].str.count(';')==5].index
recipes.loc[fltr,'prep_time'] = recipes['time_info'][recipes['time_info'].str.count(';')==5].str.split(';').str.get(0)
recipes.loc[fltr,'cook_time'] = recipes['time_info'][recipes['time_info'].str.count(';')==5].str.split(';').str.get(1)
recipes.loc[fltr,'add_time'] = recipes['time_info'][recipes['time_info'].str.count(';')==5].str.split(';').str.get(2)
recipes.loc[fltr,'ttl_time'] = recipes['time_info'][recipes['time_info'].str.count(';')==5].str.split(';').str.get(3)
recipes.loc[fltr,'servings'] = recipes['time_info'][recipes['time_info'].str.count(';')==5].str.split(';').str.get(4)
recipes.loc[fltr,'yield'] = recipes['time_info'][recipes['time_info'].str.count(';')==5].str.split(';').str.get(5)

# recipes NO ADD TIME
fltr = recipes['time_info'][recipes['time_info'].str.count(';')==4].index
recipes.loc[fltr,'prep_time'] = recipes['time_info'][recipes['time_info'].str.count(';')==4].str.split(';').str.get(0)
recipes.loc[fltr,'cook_time'] = recipes['time_info'][recipes['time_info'].str.count(';')==4].str.split(';').str.get(1)
recipes.loc[fltr,'ttl_time'] = recipes['time_info'][recipes['time_info'].str.count(';')==4].str.split(';').str.get(2)
recipes.loc[fltr,'servings'] = recipes['time_info'][recipes['time_info'].str.count(';')==4].str.split(';').str.get(3)
recipes.loc[fltr,'yield'] = recipes['time_info'][recipes['time_info'].str.count(';')==4].str.split(';').str.get(4)

# recipes NO ADD TIME, NO COOK TIME
fltr = recipes['time_info'][recipes['time_info'].str.count(';')==3].index
recipes.loc[fltr,'prep_time'] = recipes['time_info'][recipes['time_info'].str.count(';')==3].str.split(';').str.get(0)
recipes.loc[fltr,'ttl_time'] = recipes['time_info'][recipes['time_info'].str.count(';')==3].str.split(';').str.get(1)
recipes.loc[fltr,'servings'] = recipes['time_info'][recipes['time_info'].str.count(';')==3].str.split(';').str.get(2)
recipes.loc[fltr,'yield'] = recipes['time_info'][recipes['time_info'].str.count(';')==3].str.split(';').str.get(3)

# recipes NO TIME
fltr = recipes['time_info'][recipes['time_info'].str.count(';')==1].index
recipes.loc[fltr,'servings'] = recipes['time_info'][recipes['time_info'].str.count(';')==1].str.split(';').str.get(0)
recipes.loc[fltr,'yield'] = recipes['time_info'][recipes['time_info'].str.count(';')==1].str.split(';').str.get(1)

'''FORMAT TIMES as numbers'''
clmns = ['prep_time', 'cook_time', 'add_time', 'ttl_time']

for col in clmns:
    keys = list(recipes[col].unique())
    dic = {}
    for key in keys:
        if str(key)[0].isdigit():
            if 'day' not in key:
                n = re.findall('\d+', key)
                if 'hr' in key and len(n) == 1:
                    dic[key] = eval(n[0])*60
                elif len(n) == 1 and 'week' in key :
                    dic[key] = eval(n[0])*7*24*60
                elif len(n) == 1 and 'hr' not in key and 'week' not in key:
                    dic[key] = eval(n[0])
                elif len(n) == 2:
                    dic[key] = eval(n[0])*60 + eval(n[1])
            elif 'day' in key:
                n = re.findall('\d+', key)
                dic[key] = eval(n[0])*60*24
    
    
    recipes[col+'_min'] = recipes[col].replace(dic)
    
'''FORMATING nutrition'''
# replace .\n Full Nutrition
recipes['nutrition'] = recipes['nutrition'].str.replace('.\n                                Full Nutrition','')

recipes['calories'] = recipes['nutrition'].str.split(';').str.get(0)
recipes['calories'] = recipes['calories'].str.split().str.get(0)
recipes['protein'] = recipes['nutrition'].str.split(';').str.get(1)
recipes['carbs'] = recipes['nutrition'].str.split(';').str.get(2)
recipes['fat'] = recipes['nutrition'].str.split(';').str.get(3)
recipes['cholesterol'] = recipes['nutrition'].str.split(';').str.get(4)
recipes['sodium'] = recipes['nutrition'].str.split(';').str.get(5)

for i in ['protein', 'fat', 'cholesterol', 'sodium']:
    recipes[i] = recipes[i].str.replace(i,'').str.strip()

recipes['carbs'] = recipes['carbs'].str.replace('carbohydrates','').str.strip()

for i in ['protein','carbs', 'fat', 'cholesterol', 'sodium']:
    recipes['DV_'+i] = recipes[i].str.split(' ',1).str.get(1)
    recipes[i] = recipes[i].str.split(' ',1).str.get(0)

'''FORMATING stars, rating, main category'''
recipes['stars'] = recipes['stars'].str.extract('(\d.\d+|\d)').astype('float')
recipes['ratings'] = recipes['ratings'].str.split(' ',1).str.get(0).str.strip().str.replace(',','').astype('int')
recipes['category_main'] = recipes['category'].str.split('>',1).str.get(0).str.strip()
recipes['category_sub'] = recipes['category'].str.split('>',2).str.get(1).str.strip()


'''Remove recipes without categories'''
recipes = recipes[~recipes['category_main'].isnull()]

'''EXPORT TO .csv'''
pd.DataFrame.to_csv(recipes,'recipes_all_fields.csv')

# data frame for dashboard
columns = ['url', 'name', 'ratings', 'stars', 'reviews', 'servings',
'yield', 'calories', 'category_main', 'category_sub', 
'prep_time_min', 'cook_time_min', 'add_time_min', 'ttl_time_min']

pd.DataFrame.to_csv(recipes[columns],'recipes.csv')

