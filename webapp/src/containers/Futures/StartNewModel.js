/*
 * Filename: StartNewModel.js
 * Project: TomorrowNow
 * File Created: Wednesday September 21st 2022
 * Author: Corey White (smortopahri@gmail.com)
 * Maintainer: Corey White
 * -----
 * Last Modified: Thu Sep 22 2022
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

import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import { LinkContainer } from 'react-router-bootstrap';
// import { FaDataBase } from "@react-icons/all-files/fa/FaDataBase";
// import { FaSolid } from "@react-icons/all-files/fa/FaSolid";
const StartNewModel = () => {

    return (
        <Card>
            <Card.Header as="h1">FUTURES</Card.Header>
            
            <Card.Body>
                {/* <Card.Img variant="top" src="" className="fa-solid fa-tree-city fa-5x" /> */}
                <Card.Title>Get Started</Card.Title>
                <Card.Text>
                    Ready to co-develop policies that will shape the future impact of urban development in your community? Click the start button to create a new model.
                </Card.Text>
                <LinkContainer to="/futures/create">
                    <Button variant="secondary">Start</Button>
                </LinkContainer>
            </Card.Body>
        </Card>
    )
}

export default StartNewModel