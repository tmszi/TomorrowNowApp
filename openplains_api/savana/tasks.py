###############################################################################
# Filename: tasks.py                                                           #
# Project: TomorrowNow                                                         #
# File Created: Monday March 28th 2022                                         #
# Author: Corey White (smortopahri@gmail.com)                                  #
# Maintainer: Corey White                                                      #
# -----                                                                        #
# Last Modified: Tue Nov 15 2022                                               #
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


from celery import shared_task
from .utils import actinia as acp
# from actinia import *
import requests
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@shared_task()
def asyncResourceStatus(user_id, resource_id, message_type="resource_message"):
    print(f"asyncResourceStatus: starting task {user_id}, {resource_id}")
    url = f"{acp.baseUrl()}/resources/{user_id}/{resource_id}"
    r = requests.get(url, auth=acp.auth())
    data = r.json()
    print(f"asyncResourceStatus: {r.status_code}")
    print(r)
    channel_layer = get_channel_layer()
    resource_name = resource_id.replace('-', '_')
    resource_group = f"savana_{resource_name}"
    updated_status = data['status']
    if r.status_code == 200:

        resources = data['urls']['resources']
        process_log = []
        if data.get('process_log') is not None:
            process_log = data['process_log']

        print(f"""
        asyncResourceStatus Data ----
        Resource Group Name: {resource_group}
        Updated Status: {updated_status}
        Resource Url: {resources}
        """)

        response_message = {
            "type": message_type,
            "message": updated_status,
            "resource_id": resource_id,
            "resources": resources,
            "process_log": process_log
        }

        return async_to_sync(channel_layer.group_send)(resource_group, response_message)

    if r.status_code == 400:

        response_message = {
            "type": message_type,
            "message": updated_status,
            "resource_id": resource_id
        }

        return async_to_sync(channel_layer.group_send)(resource_group, response_message)


@shared_task()
def asyncModelUpdateResourceStatus(model_id, user_id, resource_id, message_type="model_setup"):
    print(f"asyncModelUpdateResourceStatus: starting task {user_id}, {resource_id}, {message_type}")
    url = f"{acp.baseUrl()}/resources/{user_id}/{resource_id}"
    r = requests.get(url, auth=acp.auth())
    data = r.json()
    print(f"asyncModelUpdateResourceStatus: {r.status_code}")
    if r.status_code == 200:
        channel_layer = get_channel_layer()
        resource_name = resource_id.replace('-', '_')
        updated_status = data['status']
        resources = data['urls']['resources']
        process_log = []
        time_delta = None
        progress = None
        message = None

        if data.get('process_log') is not None:
            process_log = data['process_log']

        if data.get('time_delta') is not None:
            time_delta = data['time_delta']

        if data.get('progress') is not None:
            progress = data['progress']

        if data.get('message') is not None:
            message = data['message']

        resource_group = f"savana_{resource_name}"

        response_message = {
            "model_id": model_id,
            "type": message_type,
            "status": updated_status,
            "resource_id": resource_id,
            "resources": resources,
            "process_log": process_log,
            "time_delta": time_delta,
            "progress": progress,
            "active_message": message
        }

        return async_to_sync(channel_layer.group_send)(resource_group, response_message)


@shared_task()
def ingestData(modelId, location, geoids):
    print("Starting Ingest")
    url = f"{acp.baseUrl()}/locations/{location}/mapsets/PERMANENT/processing_async"
    # mapset = location

    # Get Process Chain Template for FUTURES
    r = requests.get(
        f"{acp.baseUrl()}/actinia_templates/b9514dee-253e-47d9-bb5c-c65bc1a035ac",
        auth=acp.auth(),
        headers={"content-type": "application/json; charset=utf-8"}
    )

    # Set the geoids in the process chain
    template_pc = r.json()['template']
    template_pc['list'][1]['inputs'][2]['value'] = geoids
    pc = template_pc

    # Run the process chain
    r = requests.post(
        url,
        auth=acp.auth(),
        json=pc,
        headers={"content-type": "application/json; charset=utf-8"}
    )

    jsonResponse = r.json()
    print(jsonResponse)
    asyncModelUpdateResourceStatus.delay(modelId, jsonResponse['user_id'], jsonResponse['resource_id'], message_type="model_setup")
