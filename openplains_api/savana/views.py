###############################################################################
# Filename: views.py                                                           #
# Project: TomorrowNow                                                         #
# File Created: Monday March 14th 2022                                         #
# Author: Corey White (smortopahri@gmail.com)                                  #
# Maintainer: Corey White                                                      #
# -----                                                                        #
# Last Modified: Tue Nov 22 2022                                               #
# Modified By: Corey White                                                     #
# -----                                                                        #
# License: GPLv3                                                               #
#                                                                              #
# Copyright (c) 2022 TomorrowNow                                               #
#                                                                              #
# TomorrowNow is an open-source geospatial participartory modeling platform    #
# to enable stakeholder engagment in socio-environmental decision-makeing.     #
#                                                                              #
# This program is free software: you can redistribute it and/or modify         #
# it under the terms of the GNU General Public License as published by         #
# the Free Software Foundation, either version 3 of the License, or            #
# (at your option) any later version.                                          #
#                                                                              #
# This program is distributed in the hope that it will be useful,              #
# but WITHOUT ANY WARRANTY; without even the implied warranty of               #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
# GNU General Public License for more details.                                 #
#                                                                              #
# You should have received a copy of the GNU General Public License            #
# along with this program.  If not, see <https://www.gnu.org/licenses/>.       #
#                                                                              #
###############################################################################

import os
from django.core.serializers import serialize
from django.http.response import Http404
from django.shortcuts import render
from django.http import JsonResponse
from django.http import FileResponse, HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from django.views import generic
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db.models.functions import Distance
from django.middleware.csrf import get_token

from .models.OPModel import OpenPlainsModel
from .models import TestGCSResourceModel
from .models import DrainRequest
from .serializers import CreateModelSerializer, DrainRequestSerializer
from django.core.files.base import ContentFile
from django.core.cache import cache

# from .serializers import WorldBorderSerializer
from rest_framework import viewsets, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.response import Response
from knox.auth import TokenAuthentication
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.gis.geos import Point, Polygon
from .serializers import UserSerializer, OPModelSerializer

import requests
import base64

from .utils import actinia as acp


# def csrf(request):
#     return JsonResponse({'csrfToken': get_token(request)})


def ping(request):
    return JsonResponse({'result': 'OK'})


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = UserSerializer


class OpModelList(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticatedOrReadOnly,)
    # queryset = OpenPlainsModel.objects.all()
    # serializer_class = OPModelSerializer

    def get(self, request, format=None):
        models = OpenPlainsModel.objects.all()
        serializer = OPModelSerializer(models, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = CreateModelSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.create(serializer.data)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OpModelDetails(APIView):
    """View an OpenPlains model's details"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = OpenPlainsModel.objects.all()
    serializer_class = OPModelSerializer

    def get_object(self, model_id):
        try:
            return OpenPlainsModel.objects.get(slug=model_id)
        except OpenPlainsModel.DoesNotExist:
            raise Http404

    def get(self, request, model_id, format=None):
        model = self.get_object(model_id)
        serializer = OPModelSerializer(model)
        return Response(serializer.data)

    def put(self, request, model_id, format=None):
        model = self.get_object(model_id)
        serializer = OPModelSerializer(model, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, model_id, format=None):
        model = self.get_object(model_id)
        model.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def resourceStatus(user_id, resource_id):
    url = f"{acp.baseUrl()}/resources/{user_id}/{resource_id}"
    r = requests.get(url, auth=acp.auth())
    data = r.json()
    print(f"resourceStatus: {r.status_code}")
    if r.status_code == 200:
        if data['status'] == 'finished':
            print(f"Finished Resource: {data}")
            return data['urls']['resources']
        else:
            return resourceStatus(user_id, resource_id)


def gLocations(request):
    """
    Gets List of Users Avaliable Locations
    Actinia Route
    GET /locations
    """
    if request.method == 'GET':
        url = f"{acp.baseUrl()}/locations"
        r = requests.get(url, auth=acp.auth())
        print(f"Request URL: {url}")
        return JsonResponse({"response": r.json()}, safe=False)

    # TODO - Set up proper error handling and reponse messages
    return JsonResponse({"error": "gLocations View: Fix Me"})


@api_view(['POST', 'DELETE'])
@permission_classes([AllowAny])
@csrf_exempt
def gLocation(request, location_name):
    """
    Create or Delete Location
    Actinia Route
    POST /locations/{locations_name}
    DELETE /locations/{locations_name}
    """
    url = f"{acp.baseUrl()}/locations/{location_name}"
    if request.method == 'POST':
        data = request.data
        r = requests.post(url, auth=acp.auth(), json=data)
        print(f"Request URL: {url}")
        cache.delete('grass_locations')
        return JsonResponse({"response": r.json()}, safe=False)

    if request.method == 'DELETE':
        r = requests.delete(url, auth=acp.auth())
        print(f"Request URL: {url}")
        if r.status_code == 200:
            return JsonResponse({"response": r.json()}, safe=False)
        else:
            return JsonResponse({"response": r.json()}, safe=False)

    # TODO - Set up proper error handling and reponse messages
    return JsonResponse({"error": "gLocation View: Fix Me"})


def gLocationInfo(request, location_name):
    """
    Get the location projection and current computational region of the PERMANENT mapset
    Actinia Route
    GET /locations/{location_name}/info
    """
    if request.method == 'GET':
        url = f"{acp.baseUrl()}/locations/{location_name}/info"
        r = requests.get(url, auth=acp.auth())
        print(f"Request URL: {url}")
        return JsonResponse({"response": r.json()}, safe=False)

    # TODO - Set up proper error handling and reponse messages
    return JsonResponse({"error": "gLocations View: Fix Me"})


def gMapsets(request, location_name):
    """
    Get a list of all mapsets that are located in a specific location.
    Actinia Route
    GET /locations/{location_name}/mapsets
    """
    url = f"{acp.baseUrl()}/locations/{location_name}/mapsets"
    if request.method == 'GET':
        r = requests.get(url, auth=acp.auth())
        print(f"Request URL: {url}")
        print(r)
        return JsonResponse({"response": r.json()}, safe=False)

    # TODO - Set up proper error handling and reponse messages
    return JsonResponse({"error": "gMapsets View: Fix Me"})


@api_view(['POST', 'DELETE'])
@permission_classes([AllowAny])
@csrf_exempt
def gMapset(request, location_name, mapset_name):
    """
    Create or Delete Mapset
    Actinia Route
    POST /locations/{locations_name}/mapsets/{mapset_name}
    DELETE /locations/{locations_name}/mapsets/{mapset_name}
    """
    url = f"{acp.baseUrl()}/locations/{location_name}/mapsets/{mapset_name}"
    if request.method == 'POST':
        r = requests.post(url, auth=acp.auth())
        print(f"Request URL: {url}")
        # cache.delete_many(keys=cache.keys('*.grass_locations.*'))
        return JsonResponse({"response": r.json()}, safe=False)

    if request.method == 'DELETE':
        r = requests.delete(url, auth=acp.auth())
        print(f"Request URL: {url}")
        if r.status_code == 200:
            # cache.delete_many(keys=cache.keys('*.grass_locations.*'))
            return JsonResponse({"response": r.json()}, safe=False)
        else:
            return JsonResponse({"response": r.json()}, safe=False)

    # TODO - Set up proper error handling and reponse messages
    return JsonResponse({"error": "gLocation View: Fix Me"})


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([AllowAny])
@csrf_exempt
def gMapsetLock(request, location_name, mapset_name):
    """
    Create or Delete Mapset
    Actinia Route
    POST /locations/{locations_name}/mapsets/{mapset_name}/lock
    DELETE /locations/{locations_name}/mapsets/{mapset_name}lock
    """
    url = f"{acp.baseUrl()}/locations/{location_name}/mapsets/{mapset_name}/lock"

    if request.method == 'GET':
        r = requests.get(url, auth=acp.auth())
        print(f"Request URL: {url}")
        # cache.delete_many(keys=cache.keys('*.grass_locations.*'))
        return JsonResponse({"response": r.json()}, safe=False)

    if request.method == 'POST':
        r = requests.post(url, auth=acp.auth())
        print(f"Request URL: {url}")
        # cache.delete_many(keys=cache.keys('*.grass_locations.*'))
        return JsonResponse({"response": r.json()}, safe=False)

    if request.method == 'DELETE':
        r = requests.delete(url, auth=acp.auth())
        print(f"Request URL: {url}")
        if r.status_code == 200:
            # cache.delete_many(keys=cache.keys('*.grass_locations.*'))
            return JsonResponse({"response": r.json()}, safe=False)
        else:
            return JsonResponse({"response": r.json()}, safe=False)

    # TODO - Set up proper error handling and reponse messages
    return JsonResponse({"error": "gLocation View: Fix Me"})


def gMapsetInfo(request, location_name, mapset_name):
    """
    Get mapsets info.
    Actinia Route
    GET /locations/{location_name}/mapsets/{mapset_name}/info
    """
    url = f"{acp.baseUrl()}/locations/{location_name}/mapsets/{mapset_name}/info"
    if request.method == 'GET':
        r = requests.get(url, auth=acp.auth())
        print(f"Request URL: {url}")
        print(r)
        return JsonResponse({"response": r.json()}, safe=False)
    
    # TODO - Set up proper error handling and reponse messages
    return JsonResponse({"error": "gMapsets View: Fix Me"})


# Create your views here.
def gListRasters(request, location_name, mapset_name):
    """
    Get list of raster layers in mapset.
    Actinia Route
    GET /locations/{location_name}/mapsets/{mapset_name}/raster_layers
    """
    url = f"{acp.baseUrl()}/locations/{location_name}/mapsets/" \
          f"{mapset_name}/raster_layers"
    r = requests.get(url, auth=acp.auth())
    print(f"Request URL: {url}")
    return JsonResponse({"response": r.json()}, safe=False)


# Create your views here.
def gListVectors(request, location_name, mapset_name):
    """
    Get list of vector layers in mapset.
    Actinia Route
    GET /locations/{location_name}/mapsets/{mapset_name}/vector_layers
    """
    url = f"{acp.baseUrl()}/locations/{location_name}/mapsets/" \
          f"{mapset_name}/vector_layers"
    r = requests.get(url, auth=acp.auth())
    print(f"Request URL: {url}")
    print(r)
    return JsonResponse({"response": r.json()}, safe=False)


def rRenderImage(request, location_name, raster_name, mapset_name):
    """
    Get png image of raster
    Actinia Route
    GET /locations/{location_name}/mapsets/{mapset_name}/raster_layers/{raster_name}/render
    """
    print(mapset_name)
    url = f"{acp.baseUrl()}/locations/{location_name}/mapsets/" \
          f"{mapset_name}/raster_layers/{raster_name}/render"

    r = requests.get(url, auth=acp.auth(), stream=True)

    if r.status_code == 200:
        decode = base64.b64encode(r.content).decode('utf-8')
        return JsonResponse({"response": {"imagedata": decode, "raster_name": raster_name}}, safe=False)


def vRenderImage(request, location_name, vector_name, mapset_name):
    """
    Get png image of vector
    Actinia Route
    GET /locations/{location_name}/mapsets/{mapset_name}/vector_layers/{vector_name}/render
    """

    url = f"{acp.baseUrl()}/locations/{location_name}/mapsets/" \
          f"{mapset_name}/vector_layers/{vector_name}/render"

    r = requests.get(url, auth=acp.auth(), stream=True)

    if r.status_code == 200:
        decode = base64.b64encode(r.content).decode('utf-8')
        return JsonResponse({"response": {"imagedata": decode, "raster_name": vector_name}}, safe=False)


def rInfo(request, location_name, mapset_name, raster_name):
    """
    Get raster info using r.info
    Actinia Route
    GET /locations/{location_name}/mapsets/{mapset_name}/raster_layers/{raster_name}
    """

    url = f"{acp.baseUrl()}/locations/{location_name}/mapsets/" \
          f"{mapset_name}/raster_layers/{raster_name}"

    r = requests.get(url, auth=acp.auth())
    print(f"Request URL: {url}")
    return JsonResponse({"response": r.json()}, safe=False)


def vInfo(request, location_name, mapset_name, vector_name):
    """
    Get raster info using r.info
    Actinia Route
    GET /locations/{location_name}/mapsets/{mapset_name}/vector_layers/{vector_name}
    """

    url = f"{acp.baseUrl()}/locations/{location_name}/mapsets/" \
          f"{mapset_name}/vector_layers/{vector_name}"

    r = requests.get(url, auth=acp.auth())
    print(f"Request URL: {url}")
    return JsonResponse({"response": r.json()}, safe=False)


def rColors(request, location_name, mapset_name, raster_name):
    """
    Get a list of all mapsets that are located in a specific location.
    Actinia Route
    GET /locations/{location_name}/mapsets
    """
    url = f"{acp.baseUrl()}/locations/{location_name}/mapsets" \
          f"/{mapset_name}/raster_layers/{raster_name}/colors"
    if request.method == 'GET':
        r = requests.get(url, auth=acp.auth())
        print(f"Request URL: {url}")
        print(r)
        return JsonResponse({"response": r.json()}, safe=False)

    # TODO - Set up proper error handling and reponse messages
    return JsonResponse({"error": "gMapsets View: Fix Me"})


# @csrf_exempt
def rGeoTiff(request, location_name, mapset_name, raster_name):
    """
    Get GeoTiff of an existing raster map layer
    Export an existing raster map layer as GTiff or COG (if COG driver available). 
    The link to the exported raster map layer is located in the JSON response.
    Actinia Route
    POST /locations/{location_name}/mapsets/{mapset_name}/raster_layers/{raster_name}/geotiff_async
    """

    url = f"{acp.baseUrl()}/locations/{location_name}/mapsets/" \
        f"{mapset_name}/raster_layers/{raster_name}/geotiff_async_orig"

    r = requests.post(url, auth=acp.auth())

    if r.status_code == 200:
        jsonResponse = r.json()
        print(f"Response: {r.json()}")
        resource_id = jsonResponse['resource_id']

        viewResponse = {
            "response": {
                "resourceId": resource_id,
                "status": jsonResponse["status"]
            }
        }

        # r2 = requests.get(newurl, auth=acp.auth())
        # print(f"Request Image Response: {r2}")
        # storage_object = TestGCSResourceModel(user_id=userId, resource_id=resource_id)
        # decode = base64.b64encode(r2.content).decode('utf-8')
        # storage_object.geotiff_result.save(f"{userId}_{resource_id}_{raster_name}",  ContentFile(decode))
        # print("Saved to Google Cloud Storage")
        # print(storage_object.geotiff_result.storage)
        return JsonResponse(viewResponse, safe=False)


# @csrf_exempt
def streamCOG(request, raster_name, resource_id):
    print("StreamCOG: ", request)

    resource_owner = acp.currentUser()
    print("Resource Owner: ", resource_owner)
    file_name = f'{raster_name}.tif'
    resource_location = os.path.join('/actinia_core', 'resources', resource_owner, resource_id, file_name)
    print("Resource Location: ", resource_location)
    try:
        file = open(resource_location, 'rb')
        response = HttpResponse(content_type="image/tiff; application=geotiff; profile=cloud-optimized")
        response.headers['Content-Disposition'] = f'attachment; filename={file_name}'
        response.write(file.read())

    except IOError:
        response = JsonResponse({'error': 'File not exist'})

    return response


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@csrf_exempt
def rDrain(request):
    """
    r.drain
    """
    if request.method == 'GET':
        # TODO
        return JsonResponse({'route': 'GET: r.drain'})

    if request.method == 'POST':

        # Use if saving results to persistent database
        # mapset_name = "hydro"
        # url = f"{acp.baseUrl()}/locations/CONUS/mapsets/{mapset_name}/processing_async"

        # Use if running ad-hoc analysis using ephemeral database
        url = f"{acp.baseUrl()}/locations/CONUS/processing_async_export"

        print(f"Actinia Request Url: {url}")
        # body_unicode = request.body.decode('utf-8')
        print(request.data)
        coords = request.data[0]['point'].split(',')
        point = Point(float(coords[0]), float(coords[1]), srid=4326)
        db_point = point
        # point.transform(ct=3358)
        point.transform(ct=5070)
        # point.transform(ct=6542)
        print("Point", point)
        t_coords = [str(t) for t in point]
        t_coords = ",".join(t_coords)
        print("Transformed Point", t_coords)

        extent_coords = request.data[0]['extent']
        extent_ne = Point(float(extent_coords[0]), float(extent_coords[1]), srid=4326)
        extent_sw = Point(float(extent_coords[2]), float(extent_coords[3]), srid=4326)
        # extent_ne.transform(ct=3358)
        # extent_sw.transform(ct=3358)

        extent_ne.transform(ct=5070)
        extent_sw.transform(ct=5070)

        minx, miny = extent_ne
        maxx, maxy = extent_sw

        # Get HUC12 id
        huc12 = request.data[0]['huc12']
        output_huc12 = f"huc12_{huc12}"
        print("Calculating Contributing Area with HUC12", huc12)

        import_huc12 = {
            "module": "v.in.ogr",
            "flags": "",
            "id": f"v.in.ogr_hydro_{huc12}",
            "inputs": [
                {
                    "param": "input",
                    "value": "PG:host=db port=5432 dbname=actinia user=actinia password=actinia"
                },
                {
                    "param": "layer",
                    "value": "wbdhu12_a_us_september2021 — WBDHU12"
                },
                {
                    "param": "where",
                    "value": f"huc12='{huc12}'"  # This is currently dangerous an needs to be sanitized
                },
                {
                    "param": "location",
                    "value": output_huc12
                }
            ],
            "outputs": [
                {
                    "param": "output",
                    "value": output_huc12
                }
            ]
        }

        reproject = {
            "module": "v.proj",
            "id": f"v.proj_hydro_{huc12}",
            "inputs": [
                {
                    "param": "location",
                    "value": output_huc12
                },
                {
                    "param": "mapset",
                    "value": "PERMANENT"
                },
                {
                    "param": "input",
                    "value": output_huc12
                },
                {
                    "param": "smax",
                    "value": "10000"
                }
            ]
        }

        set_region = {
            "module": "g.region",
            "id": f"g.region_hydro_{huc12}",
            "inputs": [
                {
                    "param": "res",
                    "value": "30"
                },
                {
                    "param": "vector",
                    "value": output_huc12
                }
            ]
        }

        slope = {
            "module": "r.slope.aspect",
            "id": f"r.slope.aspect_{huc12}",
            "inputs": [
                {
                    "param": "elevation",
                    "value": "usgs_3dep_30m"
                },
                {
                    "param": "nprocs",
                    "value": "4"
                }
            ],
            "outputs": [
                {
                    "param": "slope",
                    "value": "slope"
                }
            ]
        }

        mean_slope = {
            "module": "r.univar",
            "id": "r.univar_slope",
            "flags": "t",
            "inputs": [
                {
                    "param": "map",
                    "value": "slope"
                },
                {
                    "param": "separator",
                    "value": "|"
                }
            ]
        }

        hydro_snap = {
            "module": "r.stream.snap",
            "id": f"r.slope.snap_{huc12}",
            "inputs": [
                {
                    "param": "input",
                    "value": "user_point"
                },
                {
                    "param": "stream_rast",
                    "value": "usgs_3dep_30m_streams"
                },
                {
                    "param": "accumulation",
                    "value": "usgs_3dep_30m_accumulation"
                },
                {
                    "param": "radius",
                    "value": "200"
                },
                {
                    "param": "memory",
                    "value": "3000"
                }
            ],
            "outputs": [
                {
                    "param": "output",
                    "value": "snapped_point"
                }
            ]
        }

        def importCOG(cog_name, year):
            return [
                {
                    "module": "r.import",
                    "id": f"r.import_{cog_name}",
                    "flags": "",
                    "inputs": [
                        {
                            "param": "input",
                            "value": f"/vsicurl/https://storage.googleapis.com/tomorrownow-actinia-dev/nlcd/{cog_name}.tif"
                        },
                        {
                            "param": "memory",
                            "value": "10000"
                        },
                        {
                            "param": "extent",
                            "value": "region"
                        },
                    ],
                    "outputs": [
                        {
                            "param": "output",
                            "value": cog_name
                        }
                    ]
                },
                {
                    "module": "r.stats",
                    "id": f"r.stats_{year}",
                    "flags": "acpl",
                    "inputs": [
                        {
                            "param": "input",
                            "value": cog_name
                        },
                        {
                            "param": "separator",
                            "value": "|"
                        },
                        {
                            "param": "null_value",
                            "value": "*"
                        },
                        {
                            "param": "nsteps",
                            "value": "255"
                        }
                    ]
                }
            ]

        grass_commands = [
            import_huc12,
            reproject,
            set_region,
            # {
            #     "module": "g.region",
            #     "id": "g.region_1804289",
            #     "inputs": [
            #         # {
            #         #     "import_descr": {
            #         #         "source": "PG:host=db port=5432 dbname=actinia user=actinia password=actinia",
            #         #         "type": "postgis",
            #         #         "vector_layer": "wbdhu12_a_us_september2021 — WBDHU12"
            #         #     },
            #         #     "param": "vector",
            #         #     "value": "wbdhuc12"
            #         # },
            #         {
            #             "param": "res",
            #             "value": "30"
            #         },
            #         {
            #             "param": "n",
            #             "value": str(maxy)
            #         },
            #         {
            #             "param": "e",
            #             "value": str(maxx)
            #         },
            #         {
            #             "param": "s",
            #             "value": str(miny)
            #         },
            #         {
            #             "param": "w",
            #             "value": str(minx)
            #         }
            #     ]
            # },
            {
                "module": "r.import",
                "id": "r.import_usgs30m_cog",
                "flags": "",
                "inputs": [
                    # {
                    #     "param": "input",
                    #     "value": "/vsicurl/https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/USGS_Seamless_DEM_13.vrt"
                    # },
                    {
                        "param": "input",
                        "value": "/vsicurl/https://storage.googleapis.com/tomorrownow-actinia-dev/SpatialData/LC20_Elev_220_cog.tif"
                        # "value": "/vsicurl/https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1/TIFF/USGS_Seamless_DEM_1.vrt"
                    },
                    {
                        "param": "resample",
                        "value": "bilinear"
                    },
                    {
                        "param": "memory",
                        "value": "10000"
                    },
                    {
                        "param": "extent",
                        "value": "region"
                    },
                ],
                "outputs": [
                    {
                        "param": "output",
                        "value": "usgs_3dep_30m"
                    }
                ]
            },
            {
                "module": "r.watershed",
                "id": "r.watershed_usgs_3dep_30",
                "inputs": [
                    {
                        "param": "elevation",
                        "value": "usgs_3dep_30m"
                    },
                    {
                        "param": "drainage",
                        "value": "usgs_3dep_30m_direction"
                    },
                    {
                        "param": "accumulation",
                        "value": "usgs_3dep_30m_accumulation" 
                    },
                    {
                        "param": "stream",
                        "value": "usgs_3dep_30m_streams"
                    },
                    {
                        "param": "threshold",
                        "value": "3000"
                    },
                    {
                        "param": "memory",
                        "value": "10000"
                    }
                ]
            },
            {
                "module": "r.thin",
                "id": "r.thin_usgs_3dep_30",
                "inputs": [
                    {
                        "param": "input",
                        "value": "usgs_3dep_30m_streams"
                    },
                    {
                        "param": "output",
                        "value": "usgs_3dep_30m_streams_thin"
                    }
                ]
            },
            {
                "module": "r.to.vect",
                "id": "r.to.vect_streams",
                "flags": "s",
                "inputs": [
                    {
                        "param": "input",
                        "value": "usgs_3dep_30m_streams_thin"
                    },
                    {
                        "param": "type",
                        "value": "line"
                    }
                ],
                "outputs": [
                    {
                        "param": "output",
                        "value": "usgs_3dep_30m_streams"
                    }
                ]
            },
            {
                "id": "v.out.ogr_streams",
                "inputs": [
                    {
                        "param": "input",
                        "value": "usgs_3dep_30m_streams"
                    },
                    {
                        "param": "type",
                        "value": "line"
                    },
                    {
                        "param": "format",
                        "value": "PostgreSQL"
                    },
                    {
                        "param": "output_type",
                        "value": "line"
                    }
                ],
                "module": "v.out.ogr",
                "outputs": [
                    {
                        "param": "output",
                        "value": "PG:host=db port=5432 dbname=actinia user=actinia password=actinia"
                    }
                ]
            },
            {
                "module": "r.circle",
                "id": "r.circle_1804289383",
                "flags": "b",
                "inputs": [
                    {
                        "param": "coordinates",
                        "value": t_coords
                    },
                    {
                        "param": "max",
                        "value": "200"
                    }
                ],
                "outputs": [
                    {
                        "param": "output",
                        "value": "circle"
                    }
                ]
            },
            ## Add drain step to get rid of r.circle by using intersecting point
            {
                "module": "r.drain",
                "id": "r.drain_1804289383",
                "flags": "dn",
                "inputs": [
                    {
                        "param": "start_coordinates",
                        "value": t_coords
                    },
                    {
                        "param": "input",
                        "value": "usgs_3dep_30m"
                    },
                    {
                        "param": "direction",
                        "value": "usgs_3dep_30m_direction"
                    },
                ],
                "outputs": [
                    {
                        "param": "output",
                        "value": "path_to_stream"
                    }
                ]
            },
            {
                "module": "r.stream.basins",
                "id": "r.stream.basins_1804289382",
                "flags": "c",
                "inputs": [
                    {
                        "param": "direction",
                        # "value": "direction_3k_10m_d",
                        "value": "usgs_3dep_30m_direction"
                    },
                    {
                        "param": "stream_rast",
                        "value": "circle"
                    },
                    {
                        "param": "memory",
                        "value": "10000"
                    }
                ],
                "outputs": [
                    {
                        "param": "basins",
                        "value": "point_basin"
                    }
                ]
            },
            {
                "module": "r.to.vect",
                "id": "r.to.vect_1804289383",
                "flags": "s",
                "inputs": [
                    {
                        "param": "input",
                        "value": "point_basin"
                    },
                    {
                        "param": "type",
                        "value": "area"
                    },
                    {
                        "param": "column",
                        "value": "value"
                    }
                ],
                "outputs": [
                    {
                        "param": "output",
                        "value": "point_basin_cloud"
                    }
                ]
            },
            {
                "module": "r.mask",
                "id": "r.mask",
                "inputs": [
                    {
                        "param": "raster",
                        "value": "point_basin"
                    },
                    {
                        "param": "maskcats",
                        "value": "*"
                    },
                    {
                        "param": "layer",
                        "value": "1"
                    }
                ]
            },
            importCOG("nlcd_2001_cog", "2001")[0],
            importCOG("nlcd_2001_cog", "2001")[1],
            importCOG("nlcd_2004_cog", "2004")[0],
            importCOG("nlcd_2004_cog", "2004")[1],
            importCOG("nlcd_2006_cog", "2006")[0],
            importCOG("nlcd_2006_cog", "2006")[1],
            importCOG("nlcd_2008_cog", "2008")[0],
            importCOG("nlcd_2008_cog", "2008")[1],
            importCOG("nlcd_2011_cog", "2011")[0],
            importCOG("nlcd_2011_cog", "2011")[1],
            importCOG("nlcd_2013_cog", "2013")[0],
            importCOG("nlcd_2013_cog", "2013")[1],
            importCOG("nlcd_2016_cog", "2016")[0],
            importCOG("nlcd_2016_cog", "2016")[1],
            importCOG("nlcd_2019_cog", "2019")[0],
            importCOG("nlcd_2019_cog", "2019")[1],
            # {
            #     "module": "r.topidx",
            #     "id": "r.topidx_1234",
            #     "inputs": [
            #         {
            #             "param": "input",
            #             "value": "usgs_3dep_30m"
            #         },
            #         {
            #             "param": "output",
            #             "value": "topidx"
            #         }
            #     ]
            # },
            # {
            #     "module": "r.stats",
            #     "id": "r.stats_topidx",
            #     "flags": "Anc",
            #     "inputs": [
            #         {
            #             "param": "input",
            #             "value": "topidx"
            #         },
            #         {
            #             "param": "separator",
            #             "value": "|"
            #         },
            #         {
            #             "param": "null_value",
            #             "value": "*"
            #         },
            #         {
            #             "param": "nsteps",
            #             "value": "255"
            #         }
            #     ]
            # },
            slope,
            mean_slope,
            {
                "module": "r.univar",
                "id": "r.univar_3dep_30m",
                "flags": "t",
                "inputs": [
                    {
                        "param": "map",
                        "value": "usgs_3dep_30m"
                    },
                    {
                        "param": "separator",
                        "value": "|"
                    }
                ]
            },
            {
                "id": "v.out.ogr_1804289383",
                "inputs": [
                    {
                        "param": "input",
                        "value": "point_basin_cloud"
                    },
                    {
                        "param": "layer",
                        "value": "1"
                    },
                    {
                        "param": "type",
                        "value": "area"
                    },
                    {
                        "param": "format",
                        "value": "PostgreSQL"
                    },
                    {
                        "param": "output_type",
                        "value": ""
                    },
                    {
                        "param": "dsco",
                        "value": ""
                    },
                    {
                        "param": "lco",
                        "value": ""
                    }
                ],
                "module": "v.out.ogr",
                "outputs": [
                    {
                        "param": "output",
                        "value": "PG:host=db port=5432 dbname=actinia user=actinia password=actinia"
                    }
                ]
            },
            {
                "id": "r.mask_1804289383",
                "flags": "r",
                "inputs": [],
                "module": "r.mask",
                "outputs": []
            }
        ]
        pc = acp.create_actinia_process_chain(grass_commands)
        print(f"Process Chain: {pc}")
        r = requests.post(
            url, auth=acp.auth(),
            json=pc,
            headers={"content-type": "application/json; charset=utf-8"}
        )
        jsonResponse = r.json()
        print(f"Response: {r.json()}")
        requestModel = DrainRequestSerializer(data={"point": db_point, "huc12": huc12}, context={'request': request})
        if (requestModel.is_valid()):
            print("serializer data:", requestModel.validated_data)
            return JsonResponse({"savana_response": requestModel.data, "response": jsonResponse}, status=status.HTTP_201_CREATED)
        else:
            return JsonResponse({'route': 'r.drain', 'params': request.data, 'pc': pc, 'response': jsonResponse, 'errors': requestModel.errors})


def gModules(request):
    """
    Get a list of all grass modules that are avaliable to user.
    Actinia Route
    GET /grass_modules
    Parameters
        tag
        category
        family (d,db,g,i,m,ps,r,r3,t,test,v)
        record : set to 'full' if you want full module response

    """

    url = f"{acp.baseUrl()}/grass_modules"
    if request.method == 'GET':
        query_params = request.GET
        r = requests.get(url, auth=acp.auth(), params=query_params)
        print(f"Request URL: {url}")
        print(r)
        return JsonResponse({"response": r.json()}, safe=False)

    # TODO - Set up proper error handling and reponse messages
    return JsonResponse({"error": "gModules View: Fix Me"})


def gModule(request, grassmodule):
    """
    Gets details about a Grass Module.
    Actinia Route
    GET /grass_modules/{grassmodule}
    """

    url = f"{acp.baseUrl()}/grass_modules/{grassmodule}"
    if request.method == 'GET':
        r = requests.get(url, auth=acp.auth())
        print(f"Request URL: {url}")
        print(r)
        if r.status_code == 200:
            return JsonResponse({"response": r.json()}, safe=False)

        if r.status_code == 400:
            return JsonResponse({"status": 400, "error": "gModules View: Fix Me"})

    # TODO - Set up proper error handling and reponse messages
    return JsonResponse({"error": "gModules View: Fix Me"})
