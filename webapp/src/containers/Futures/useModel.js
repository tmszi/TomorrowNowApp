/*
 * Filename: useModel.js
 * Project: TomorrowNow
 * File Created: Tuesday October 18th 2022
 * Author: Corey White (smortopahri@gmail.com)
 * Maintainer: Corey White
 * -----
 * Last Modified: Tue Oct 18 2022
 * Modified By: Corey White
 * -----
 * License: GPLv3
 * 
 * Copyright (c) 2022 TomorrowNow
 * 
 * TomorrowNow is an open-source geospatial participartory modeling platform
 * to enable stakeholder engagment in socio-environmental decision-makeing.
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 * 
 */
import { settings } from "../../components/Grass/Settings"
import { useDataSource } from "../../components/Grass/Utils"

export const useModel = ({modelId}) => {
    const URL = `${settings.ACTINIA_BASE_URL}/model/${modelId}`
    const fetchModel = async(params) => {
        const response = await fetch(URL)
        return response
    }

    const {data, errors, isloading } = useDataSource({fetchModel, params: [modelId]})

    return {data, errors, isloading }
}
