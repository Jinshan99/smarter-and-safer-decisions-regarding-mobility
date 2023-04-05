import pandas as pd
import urllib.request
import json
import os
import io
from google.cloud import vision
from PIL import Image, ImageDraw

############################################### IMAGE RETREIVAL ###############################################

API_KEY = '&key=' + 'AIzaSyD9GpUtJVQ1p4mHKJEp-n2paA2Z8ANI-ao'
ImageStorePath = r'retrieved_street_view_images/' 
PrevImage = []

"""
MetaParse(MetaUrl) captures date and pano_id from each street view image. This capturing of metadata is done 
to prevent google from downloading duplicate images. Here, we grab the metadata first and store it in a global
list PrevImage. Hence, if an image is already downloaded, GetStreetImages will not download it again as it
checks PrevImage. 
"""

def MetaParse(MetaUrl):
	response = urllib.request.urlopen(MetaUrl)
	jsonData = json.loads(response.read())

	if jsonData['status'] == "OK":
		if 'date' in jsonData:
			return (jsonData['date'], jsonData['pano_id'])
		else:
			return (None, jsonData['pano_id'])
	else:
		return (None, None)

#Extracts metadata and downloads images based on provided Latitude, Longitude, and orientation

def GetStreetImages(Lat,Lon,Head,File,SaveLoc):
	base = r"https://maps.googleapis.com/maps/api/streetview"
	size = r"?size=1200x800&fov=60&location="
	end = str(Lat) + "," + str(Lon) + "&heading=" + str(Head) + API_KEY
	MyUrl = base + size + end
	f_name = File + ".jpg"
	MetaUrl = base + r"/metadata" + size + end
	meta_list = list(MetaParse(MetaUrl))
	if (meta_list[1], Head) not in PrevImage and meta_list[0] is not None:
		urllib.request.urlretrieve(MyUrl, os.path.join(SaveLoc,f_name))
		meta_list.append(f_name)
		PrevImage.append((meta_list[1], Head))
	else:
		meta_list.append(None)

	return meta_list

# Read Cleaned Dataset of Location and create a list of tuples to represent Latitde and Longitude
df = pd.read_csv('dataset/LA_Crime_Data_Location_Time.csv')
df['Coordinates'] = list(zip(df.LAT, df.LON))
Coordinate_List = df.Coordinates.values.tolist()

# To store resulting metadata
image_list = []
count = 0

# Iterate over the coordinate list and draw images
for i in Coordinate_List[:100]:
	count += 1
	f_name = 'Image_' + str(count)
	print('Processing image:', count)
	temp = GetStreetImages(Lat=i[0],Lon=i[1],Head=97.00,File=f_name,SaveLoc=ImageStorePath)
	if temp[2] is not None:
		image_list.append(temp)

print('\nStreet View Images Retrieval Complete'.upper())


############################################### OBJECT DETECTION ############################################

print('\nPERFORMING OBJECT DETECTION\n')
result_path = 'detected_objects'

def draw_boundary_normalized(image_store_path, index, image_file, vertices, caption=''):
	pil_image = Image.open(image_file)
	draw = ImageDraw.Draw(pil_image)
	xys = [(vertex.x * pil_image.size[0], vertex.y * pil_image.size[1]) for vertex in vertices]
	xys.append(xys[0])
	draw.line(xys, fill=(255, 255, 0), width=10)
	draw.text((xys[0][0], xys[0][1]-45), caption)
	pil_image = pil_image.save(os.path.join(image_store_path, 'object'+str(index)+'.jpg'))


#Instantiating client
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'dsci-560-safety-app-ad956494dd42.json'
client = vision.ImageAnnotatorClient()

# Preparing image
image_path = 'retrieved_street_view_images/'
image_list = list()

for images in os.listdir(image_path):
	if images.endswith('.jpg'):
		image_list.append(images)

for image in image_list:
	image_url = os.path.join(image_path, image)
	with io.open(image_url, 'rb') as image_file:
		content = image_file.read()

	street_view_image = vision.Image(content=content)

	objects = client.object_localization(image=street_view_image).localized_object_annotations

	image_store_path = os.path.join(result_path, image)
	os.mkdir(image_store_path)

	print('Number of objects found in', image, ':', len(objects))

	for index, object_ in enumerate(objects):
		print('{} (confidence: {})'.format(object_.name, object_.score))
		draw_boundary_normalized(image_store_path, index, image_url, object_.bounding_poly.normalized_vertices, object_.name)

	print('\n')


