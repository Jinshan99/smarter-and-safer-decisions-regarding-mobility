#!/usr/bin/env python
# coding: utf-8

# In[32]:


from flask import Flask, jsonify, request
import datetime
import json
import joblib
from flask_cors import CORS
from scipy.spatial.distance import cdist
from math import radians, cos, sin, asin, sqrt


# In[31]:


app = Flask(__name__, static_url_path='')
CORS(app)

@app.route('/predict', methods = ['POST'])
def predict():
    data = request.get_json()
    g_LAT_LON = data.get('route_points')
    crime = data.get('crime_type')
    ### my code for file
    def load_json_file(file_path1, file_path2, file_path3):
        with open(file_path1, 'r') as file1:
            police_coordinate = json.load(file1)
        with open(file_path2, 'r') as file2:
            hospital_coordinate = json.load(file2)
        with open(file_path3, 'r') as file3:
            crime_locations = json.load(file3)
        return police_coordinate, hospital_coordinate, crime_locations

    ### my code for year, month, day, time
    def current_datetime():
        current_time = datetime.datetime.now()
        year = current_time.year
        month = current_time.month
        day = current_time.day
        hour = current_time.hour
        def categorize_time(hour):
            categories = None
            if hour >= 0 and hour < 3:
                categories = 4
            elif hour >= 3 and hour < 6:
                categories = 1
            elif hour >= 6 and hour < 9:
                categories = 6
            elif hour >= 9 and hour < 12:
                categories = 4
            elif hour >= 12 and hour < 15:
                categories = 0
            elif hour >= 15 and hour < 18:
                categories = 3
            elif hour >= 18 and hour < 21:
                categories = 2
            else:
                categories = 5
            return categories

        return year, month, day, categorize_time(hour)
    
    ### calculate distance to the closest police office/hospital
    def calculate_hospital_policeman(p_loc, h_loc):
        # calculate distance matrix using cdist
        police_distances = cdist(g_LAT_LON, p_loc)
        hospital_distances = cdist(g_LAT_LON, h_loc)
        # get minimum distance for each row in A
        p_min_distances = police_distances.min(axis=1)
        h_min_distances = hospital_distances.min(axis=1)
        return p_min_distances, h_min_distances
    

    ### calculate danger level
    def dangerous_level_check():
        dangerous_level = []
        for i in range(len(g_LAT_LON)):
            lat_start, lat_end, lon_start, lon_end, step = 33.706, 34.335, -118.668, -118.155, 0.0015
            current_Lat = g_LAT_LON[i][0]
            current_Lon = g_LAT_LON[i][1]
            index_Lat = int((current_Lat - lat_start) / step)
            index_Lon = int((current_Lon - lon_start) / step)
            if index_Lon > 342 or index_Lat > 420:
                safety_value = 40
            else:
                safety_value = regions[index_Lat][index_Lon]
            if safety_value >= 1600:
                dangerous_level.append(1)
            elif safety_value >= 530:
                dangerous_level.append(0)
            elif safety_value >= 40:
                dangerous_level.append(2)
            else: 
                dangerous_level.append(3)
        return dangerous_level
    
    ### process section
    police, hospital, regions = load_json_file("C:/Users/wn199/Desktop/DSCI560project/DSCI560project/src/backend/policecoordinates.json", "C:/Users/wn199/Desktop/DSCI560project/DSCI560project/src/backend/hospitalcoordinates.json", "C:/Users/wn199/Desktop/DSCI560project/DSCI560project/src/backend/location.json")
    p_list, h_list = calculate_hospital_policeman(police, hospital)
    year, month, day, time = current_datetime()
    danger_list = dangerous_level_check()
    
    ### make input of model
    def make_input_for_model():
        output = []
        for i in range(len(g_LAT_LON)):
            each_data = [g_LAT_LON[i][0], g_LAT_LON[i][1], day, month, year, p_list[i], h_list[i], danger_list[i], time]
            output.append(each_data)
        return output
    predict_x = make_input_for_model()

    def find_safe_region(intput_i):
        lat_start, lat_end, lon_start, lon_end, step = 33.706, 34.335, -118.668, -118.155, 0.0015
        current_Lat = g_LAT_LON[intput_i][0]
        current_Lon = g_LAT_LON[intput_i][1]
        index_Lat = int((current_Lat - lat_start) / step)
        index_Lon = int((current_Lon - lon_start) / step)
        answer = []
        if index_Lon > 342 or index_Lat > 420:
            answer = [current_Lat, current_Lon]
        else:
            if index_Lat >= 1 and index_Lon >= 1:
                safe_list_score =  [regions[index_Lat - 1][index_Lon - 1], regions[index_Lat - 1][index_Lon], regions[index_Lat - 1][index_Lon + 1],
                                    regions[index_Lat][index_Lon - 1], regions[index_Lat][index_Lon], regions[index_Lat][index_Lon + 1],
                                    regions[index_Lat + 1][index_Lon - 1], regions[index_Lat + 1][index_Lon], regions[index_Lat + 1][index_Lon + 1]]
                min_score = min(safe_list_score)
                min_index = safe_list_score.index(min_score)
                if min_index < 3:
                    if min_index == 0:
                        answer = [g_LAT_LON[i][0] - 0.0015, g_LAT_LON[i][1] - 0.0015]
                    elif min_index == 1:
                        answer = [g_LAT_LON[i][0] - 0.0015, g_LAT_LON[i][1]]
                    else:
                        answer = [g_LAT_LON[i][0] - 0.0015, g_LAT_LON[i][1] + 0.0015]
                elif min_index < 6:
                    if min_index == 3:
                        answer = [g_LAT_LON[i][0], g_LAT_LON[i][1] - 0.0015]
                    elif min_index == 4:
                        answer = [g_LAT_LON[i][0], g_LAT_LON[i][1]]
                    else:
                        answer = [g_LAT_LON[i][0], g_LAT_LON[i][1] + 0.0015]
                elif min_index < 9:
                    if min_index == 6:
                        answer = [g_LAT_LON[i][0] + 0.0015, g_LAT_LON[i][1] - 0.0015]
                    elif min_index == 7:
                        answer = [g_LAT_LON[i][0] + 0.0015, g_LAT_LON[i][1]]
                    else:
                        answer = [g_LAT_LON[i][0] + 0.0015, g_LAT_LON[i][1] + 0.0015]
        return answer

    ### import my own model
    model = joblib.load("C:/Users/wn199/Desktop/DSCI560project/DSCI560project/src/backend/crime_model.joblib")
    prediction = model.predict(predict_x)
    problem_point = []
    for i in range(len(prediction)):
        if crime == "Assaults and threats":
            if prediction[i] == "Assaults and threats":
                safe_spot = find_safe_region(i)
                problem_point.append(safe_spot)
        elif crime == "Robbery and related crimes":
            if prediction[i] == "Robbery and related crimes" or prediction[i] == "Property crimes":
                safe_spot = find_safe_region(i)
                problem_point.append(safe_spot)
        else:
            if prediction[i] == "others" or prediction[i] == "Domestic violence":
                safe_spot = find_safe_region(i)
                problem_point.append(safe_spot)

    ### return my predictions
    #return {"member": ["Memberr1"]}
    return jsonify({'predictions': problem_point})

if __name__ == '__main__':
    app.run(debug = True)


# In[ ]:





# In[ ]:





# In[ ]:




