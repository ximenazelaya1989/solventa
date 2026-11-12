/*
   Licensed to the Apache Software Foundation (ASF) under one or more
   contributor license agreements.  See the NOTICE file distributed with
   this work for additional information regarding copyright ownership.
   The ASF licenses this file to You under the Apache License, Version 2.0
   (the "License"); you may not use this file except in compliance with
   the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/
$(document).ready(function() {

    $(".click-title").mouseenter( function(    e){
        e.preventDefault();
        this.style.cursor="pointer";
    });
    $(".click-title").mousedown( function(event){
        event.preventDefault();
    });

    // Ugly code while this script is shared among several pages
    try{
        refreshHitsPerSecond(true);
    } catch(e){}
    try{
        refreshResponseTimeOverTime(true);
    } catch(e){}
    try{
        refreshResponseTimePercentiles();
    } catch(e){}
});


var responseTimePercentilesInfos = {
        data: {"result": {"minY": 33.0, "minX": 0.0, "maxY": 796.0, "series": [{"data": [[0.0, 33.0], [0.1, 38.0], [0.2, 39.0], [0.3, 40.0], [0.4, 41.0], [0.5, 41.0], [0.6, 42.0], [0.7, 42.0], [0.8, 43.0], [0.9, 43.0], [1.0, 44.0], [1.1, 44.0], [1.2, 44.0], [1.3, 45.0], [1.4, 45.0], [1.5, 45.0], [1.6, 45.0], [1.7, 45.0], [1.8, 46.0], [1.9, 46.0], [2.0, 46.0], [2.1, 46.0], [2.2, 46.0], [2.3, 46.0], [2.4, 46.0], [2.5, 46.0], [2.6, 47.0], [2.7, 47.0], [2.8, 47.0], [2.9, 47.0], [3.0, 47.0], [3.1, 47.0], [3.2, 47.0], [3.3, 48.0], [3.4, 48.0], [3.5, 48.0], [3.6, 48.0], [3.7, 48.0], [3.8, 48.0], [3.9, 48.0], [4.0, 48.0], [4.1, 48.0], [4.2, 49.0], [4.3, 49.0], [4.4, 49.0], [4.5, 49.0], [4.6, 49.0], [4.7, 49.0], [4.8, 49.0], [4.9, 49.0], [5.0, 49.0], [5.1, 49.0], [5.2, 49.0], [5.3, 49.0], [5.4, 50.0], [5.5, 50.0], [5.6, 50.0], [5.7, 50.0], [5.8, 50.0], [5.9, 50.0], [6.0, 50.0], [6.1, 50.0], [6.2, 50.0], [6.3, 50.0], [6.4, 50.0], [6.5, 50.0], [6.6, 50.0], [6.7, 51.0], [6.8, 51.0], [6.9, 51.0], [7.0, 51.0], [7.1, 51.0], [7.2, 51.0], [7.3, 51.0], [7.4, 51.0], [7.5, 51.0], [7.6, 51.0], [7.7, 51.0], [7.8, 51.0], [7.9, 51.0], [8.0, 51.0], [8.1, 51.0], [8.2, 52.0], [8.3, 52.0], [8.4, 52.0], [8.5, 52.0], [8.6, 52.0], [8.7, 52.0], [8.8, 52.0], [8.9, 52.0], [9.0, 52.0], [9.1, 52.0], [9.2, 52.0], [9.3, 52.0], [9.4, 52.0], [9.5, 52.0], [9.6, 52.0], [9.7, 52.0], [9.8, 52.0], [9.9, 53.0], [10.0, 53.0], [10.1, 53.0], [10.2, 53.0], [10.3, 53.0], [10.4, 53.0], [10.5, 53.0], [10.6, 53.0], [10.7, 53.0], [10.8, 53.0], [10.9, 53.0], [11.0, 53.0], [11.1, 53.0], [11.2, 53.0], [11.3, 53.0], [11.4, 53.0], [11.5, 53.0], [11.6, 53.0], [11.7, 53.0], [11.8, 53.0], [11.9, 53.0], [12.0, 53.0], [12.1, 53.0], [12.2, 54.0], [12.3, 54.0], [12.4, 54.0], [12.5, 54.0], [12.6, 54.0], [12.7, 54.0], [12.8, 54.0], [12.9, 54.0], [13.0, 54.0], [13.1, 54.0], [13.2, 54.0], [13.3, 54.0], [13.4, 54.0], [13.5, 54.0], [13.6, 54.0], [13.7, 54.0], [13.8, 54.0], [13.9, 54.0], [14.0, 54.0], [14.1, 54.0], [14.2, 54.0], [14.3, 54.0], [14.4, 54.0], [14.5, 54.0], [14.6, 54.0], [14.7, 54.0], [14.8, 55.0], [14.9, 55.0], [15.0, 55.0], [15.1, 55.0], [15.2, 55.0], [15.3, 55.0], [15.4, 55.0], [15.5, 55.0], [15.6, 55.0], [15.7, 55.0], [15.8, 55.0], [15.9, 55.0], [16.0, 55.0], [16.1, 55.0], [16.2, 55.0], [16.3, 55.0], [16.4, 55.0], [16.5, 55.0], [16.6, 55.0], [16.7, 55.0], [16.8, 55.0], [16.9, 55.0], [17.0, 55.0], [17.1, 55.0], [17.2, 55.0], [17.3, 55.0], [17.4, 55.0], [17.5, 55.0], [17.6, 55.0], [17.7, 55.0], [17.8, 55.0], [17.9, 56.0], [18.0, 56.0], [18.1, 56.0], [18.2, 56.0], [18.3, 56.0], [18.4, 56.0], [18.5, 56.0], [18.6, 56.0], [18.7, 56.0], [18.8, 56.0], [18.9, 56.0], [19.0, 56.0], [19.1, 56.0], [19.2, 56.0], [19.3, 56.0], [19.4, 56.0], [19.5, 56.0], [19.6, 56.0], [19.7, 56.0], [19.8, 56.0], [19.9, 56.0], [20.0, 56.0], [20.1, 56.0], [20.2, 56.0], [20.3, 56.0], [20.4, 56.0], [20.5, 56.0], [20.6, 56.0], [20.7, 56.0], [20.8, 56.0], [20.9, 56.0], [21.0, 56.0], [21.1, 57.0], [21.2, 57.0], [21.3, 57.0], [21.4, 57.0], [21.5, 57.0], [21.6, 57.0], [21.7, 57.0], [21.8, 57.0], [21.9, 57.0], [22.0, 57.0], [22.1, 57.0], [22.2, 57.0], [22.3, 57.0], [22.4, 57.0], [22.5, 57.0], [22.6, 57.0], [22.7, 57.0], [22.8, 57.0], [22.9, 57.0], [23.0, 57.0], [23.1, 57.0], [23.2, 57.0], [23.3, 57.0], [23.4, 57.0], [23.5, 57.0], [23.6, 57.0], [23.7, 57.0], [23.8, 57.0], [23.9, 57.0], [24.0, 57.0], [24.1, 57.0], [24.2, 57.0], [24.3, 57.0], [24.4, 57.0], [24.5, 57.0], [24.6, 57.0], [24.7, 58.0], [24.8, 58.0], [24.9, 58.0], [25.0, 58.0], [25.1, 58.0], [25.2, 58.0], [25.3, 58.0], [25.4, 58.0], [25.5, 58.0], [25.6, 58.0], [25.7, 58.0], [25.8, 58.0], [25.9, 58.0], [26.0, 58.0], [26.1, 58.0], [26.2, 58.0], [26.3, 58.0], [26.4, 58.0], [26.5, 58.0], [26.6, 58.0], [26.7, 58.0], [26.8, 58.0], [26.9, 58.0], [27.0, 58.0], [27.1, 58.0], [27.2, 58.0], [27.3, 58.0], [27.4, 58.0], [27.5, 58.0], [27.6, 58.0], [27.7, 58.0], [27.8, 58.0], [27.9, 58.0], [28.0, 58.0], [28.1, 58.0], [28.2, 58.0], [28.3, 58.0], [28.4, 58.0], [28.5, 58.0], [28.6, 59.0], [28.7, 59.0], [28.8, 59.0], [28.9, 59.0], [29.0, 59.0], [29.1, 59.0], [29.2, 59.0], [29.3, 59.0], [29.4, 59.0], [29.5, 59.0], [29.6, 59.0], [29.7, 59.0], [29.8, 59.0], [29.9, 59.0], [30.0, 59.0], [30.1, 59.0], [30.2, 59.0], [30.3, 59.0], [30.4, 59.0], [30.5, 59.0], [30.6, 59.0], [30.7, 59.0], [30.8, 59.0], [30.9, 59.0], [31.0, 59.0], [31.1, 59.0], [31.2, 59.0], [31.3, 59.0], [31.4, 59.0], [31.5, 59.0], [31.6, 59.0], [31.7, 59.0], [31.8, 59.0], [31.9, 59.0], [32.0, 59.0], [32.1, 59.0], [32.2, 59.0], [32.3, 59.0], [32.4, 59.0], [32.5, 59.0], [32.6, 60.0], [32.7, 60.0], [32.8, 60.0], [32.9, 60.0], [33.0, 60.0], [33.1, 60.0], [33.2, 60.0], [33.3, 60.0], [33.4, 60.0], [33.5, 60.0], [33.6, 60.0], [33.7, 60.0], [33.8, 60.0], [33.9, 60.0], [34.0, 60.0], [34.1, 60.0], [34.2, 60.0], [34.3, 60.0], [34.4, 60.0], [34.5, 60.0], [34.6, 60.0], [34.7, 60.0], [34.8, 60.0], [34.9, 60.0], [35.0, 60.0], [35.1, 60.0], [35.2, 60.0], [35.3, 60.0], [35.4, 60.0], [35.5, 60.0], [35.6, 60.0], [35.7, 60.0], [35.8, 60.0], [35.9, 60.0], [36.0, 60.0], [36.1, 60.0], [36.2, 60.0], [36.3, 60.0], [36.4, 60.0], [36.5, 60.0], [36.6, 60.0], [36.7, 61.0], [36.8, 61.0], [36.9, 61.0], [37.0, 61.0], [37.1, 61.0], [37.2, 61.0], [37.3, 61.0], [37.4, 61.0], [37.5, 61.0], [37.6, 61.0], [37.7, 61.0], [37.8, 61.0], [37.9, 61.0], [38.0, 61.0], [38.1, 61.0], [38.2, 61.0], [38.3, 61.0], [38.4, 61.0], [38.5, 61.0], [38.6, 61.0], [38.7, 61.0], [38.8, 61.0], [38.9, 61.0], [39.0, 61.0], [39.1, 61.0], [39.2, 61.0], [39.3, 61.0], [39.4, 61.0], [39.5, 61.0], [39.6, 61.0], [39.7, 61.0], [39.8, 61.0], [39.9, 61.0], [40.0, 61.0], [40.1, 61.0], [40.2, 61.0], [40.3, 61.0], [40.4, 61.0], [40.5, 61.0], [40.6, 61.0], [40.7, 61.0], [40.8, 61.0], [40.9, 61.0], [41.0, 61.0], [41.1, 61.0], [41.2, 61.0], [41.3, 62.0], [41.4, 62.0], [41.5, 62.0], [41.6, 62.0], [41.7, 62.0], [41.8, 62.0], [41.9, 62.0], [42.0, 62.0], [42.1, 62.0], [42.2, 62.0], [42.3, 62.0], [42.4, 62.0], [42.5, 62.0], [42.6, 62.0], [42.7, 62.0], [42.8, 62.0], [42.9, 62.0], [43.0, 62.0], [43.1, 62.0], [43.2, 62.0], [43.3, 62.0], [43.4, 62.0], [43.5, 62.0], [43.6, 62.0], [43.7, 62.0], [43.8, 62.0], [43.9, 62.0], [44.0, 62.0], [44.1, 62.0], [44.2, 62.0], [44.3, 62.0], [44.4, 62.0], [44.5, 62.0], [44.6, 62.0], [44.7, 62.0], [44.8, 62.0], [44.9, 62.0], [45.0, 62.0], [45.1, 62.0], [45.2, 62.0], [45.3, 62.0], [45.4, 62.0], [45.5, 63.0], [45.6, 63.0], [45.7, 63.0], [45.8, 63.0], [45.9, 63.0], [46.0, 63.0], [46.1, 63.0], [46.2, 63.0], [46.3, 63.0], [46.4, 63.0], [46.5, 63.0], [46.6, 63.0], [46.7, 63.0], [46.8, 63.0], [46.9, 63.0], [47.0, 63.0], [47.1, 63.0], [47.2, 63.0], [47.3, 63.0], [47.4, 63.0], [47.5, 63.0], [47.6, 63.0], [47.7, 63.0], [47.8, 63.0], [47.9, 63.0], [48.0, 63.0], [48.1, 63.0], [48.2, 63.0], [48.3, 63.0], [48.4, 63.0], [48.5, 63.0], [48.6, 63.0], [48.7, 63.0], [48.8, 63.0], [48.9, 63.0], [49.0, 63.0], [49.1, 63.0], [49.2, 63.0], [49.3, 63.0], [49.4, 63.0], [49.5, 64.0], [49.6, 64.0], [49.7, 64.0], [49.8, 64.0], [49.9, 64.0], [50.0, 64.0], [50.1, 64.0], [50.2, 64.0], [50.3, 64.0], [50.4, 64.0], [50.5, 64.0], [50.6, 64.0], [50.7, 64.0], [50.8, 64.0], [50.9, 64.0], [51.0, 64.0], [51.1, 64.0], [51.2, 64.0], [51.3, 64.0], [51.4, 64.0], [51.5, 64.0], [51.6, 64.0], [51.7, 64.0], [51.8, 64.0], [51.9, 64.0], [52.0, 64.0], [52.1, 64.0], [52.2, 64.0], [52.3, 64.0], [52.4, 64.0], [52.5, 64.0], [52.6, 64.0], [52.7, 64.0], [52.8, 64.0], [52.9, 64.0], [53.0, 64.0], [53.1, 64.0], [53.2, 64.0], [53.3, 64.0], [53.4, 64.0], [53.5, 64.0], [53.6, 64.0], [53.7, 64.0], [53.8, 64.0], [53.9, 65.0], [54.0, 65.0], [54.1, 65.0], [54.2, 65.0], [54.3, 65.0], [54.4, 65.0], [54.5, 65.0], [54.6, 65.0], [54.7, 65.0], [54.8, 65.0], [54.9, 65.0], [55.0, 65.0], [55.1, 65.0], [55.2, 65.0], [55.3, 65.0], [55.4, 65.0], [55.5, 65.0], [55.6, 65.0], [55.7, 65.0], [55.8, 65.0], [55.9, 65.0], [56.0, 65.0], [56.1, 65.0], [56.2, 65.0], [56.3, 65.0], [56.4, 65.0], [56.5, 65.0], [56.6, 65.0], [56.7, 65.0], [56.8, 65.0], [56.9, 65.0], [57.0, 65.0], [57.1, 65.0], [57.2, 65.0], [57.3, 65.0], [57.4, 65.0], [57.5, 65.0], [57.6, 65.0], [57.7, 65.0], [57.8, 65.0], [57.9, 65.0], [58.0, 65.0], [58.1, 65.0], [58.2, 65.0], [58.3, 65.0], [58.4, 65.0], [58.5, 66.0], [58.6, 66.0], [58.7, 66.0], [58.8, 66.0], [58.9, 66.0], [59.0, 66.0], [59.1, 66.0], [59.2, 66.0], [59.3, 66.0], [59.4, 66.0], [59.5, 66.0], [59.6, 66.0], [59.7, 66.0], [59.8, 66.0], [59.9, 66.0], [60.0, 66.0], [60.1, 66.0], [60.2, 66.0], [60.3, 66.0], [60.4, 66.0], [60.5, 66.0], [60.6, 66.0], [60.7, 66.0], [60.8, 66.0], [60.9, 66.0], [61.0, 66.0], [61.1, 66.0], [61.2, 66.0], [61.3, 66.0], [61.4, 66.0], [61.5, 66.0], [61.6, 66.0], [61.7, 66.0], [61.8, 66.0], [61.9, 66.0], [62.0, 66.0], [62.1, 66.0], [62.2, 66.0], [62.3, 66.0], [62.4, 66.0], [62.5, 66.0], [62.6, 66.0], [62.7, 66.0], [62.8, 67.0], [62.9, 67.0], [63.0, 67.0], [63.1, 67.0], [63.2, 67.0], [63.3, 67.0], [63.4, 67.0], [63.5, 67.0], [63.6, 67.0], [63.7, 67.0], [63.8, 67.0], [63.9, 67.0], [64.0, 67.0], [64.1, 67.0], [64.2, 67.0], [64.3, 67.0], [64.4, 67.0], [64.5, 67.0], [64.6, 67.0], [64.7, 67.0], [64.8, 67.0], [64.9, 67.0], [65.0, 67.0], [65.1, 67.0], [65.2, 67.0], [65.3, 67.0], [65.4, 67.0], [65.5, 67.0], [65.6, 67.0], [65.7, 67.0], [65.8, 67.0], [65.9, 67.0], [66.0, 67.0], [66.1, 67.0], [66.2, 67.0], [66.3, 67.0], [66.4, 67.0], [66.5, 67.0], [66.6, 67.0], [66.7, 67.0], [66.8, 68.0], [66.9, 68.0], [67.0, 68.0], [67.1, 68.0], [67.2, 68.0], [67.3, 68.0], [67.4, 68.0], [67.5, 68.0], [67.6, 68.0], [67.7, 68.0], [67.8, 68.0], [67.9, 68.0], [68.0, 68.0], [68.1, 68.0], [68.2, 68.0], [68.3, 68.0], [68.4, 68.0], [68.5, 68.0], [68.6, 68.0], [68.7, 68.0], [68.8, 68.0], [68.9, 68.0], [69.0, 68.0], [69.1, 68.0], [69.2, 68.0], [69.3, 68.0], [69.4, 68.0], [69.5, 68.0], [69.6, 68.0], [69.7, 68.0], [69.8, 68.0], [69.9, 68.0], [70.0, 68.0], [70.1, 68.0], [70.2, 68.0], [70.3, 68.0], [70.4, 69.0], [70.5, 69.0], [70.6, 69.0], [70.7, 69.0], [70.8, 69.0], [70.9, 69.0], [71.0, 69.0], [71.1, 69.0], [71.2, 69.0], [71.3, 69.0], [71.4, 69.0], [71.5, 69.0], [71.6, 69.0], [71.7, 69.0], [71.8, 69.0], [71.9, 69.0], [72.0, 69.0], [72.1, 69.0], [72.2, 69.0], [72.3, 69.0], [72.4, 69.0], [72.5, 69.0], [72.6, 69.0], [72.7, 69.0], [72.8, 69.0], [72.9, 69.0], [73.0, 69.0], [73.1, 69.0], [73.2, 69.0], [73.3, 69.0], [73.4, 69.0], [73.5, 69.0], [73.6, 70.0], [73.7, 70.0], [73.8, 70.0], [73.9, 70.0], [74.0, 70.0], [74.1, 70.0], [74.2, 70.0], [74.3, 70.0], [74.4, 70.0], [74.5, 70.0], [74.6, 70.0], [74.7, 70.0], [74.8, 70.0], [74.9, 70.0], [75.0, 70.0], [75.1, 70.0], [75.2, 70.0], [75.3, 70.0], [75.4, 70.0], [75.5, 70.0], [75.6, 70.0], [75.7, 70.0], [75.8, 70.0], [75.9, 70.0], [76.0, 70.0], [76.1, 70.0], [76.2, 70.0], [76.3, 70.0], [76.4, 71.0], [76.5, 71.0], [76.6, 71.0], [76.7, 71.0], [76.8, 71.0], [76.9, 71.0], [77.0, 71.0], [77.1, 71.0], [77.2, 71.0], [77.3, 71.0], [77.4, 71.0], [77.5, 71.0], [77.6, 71.0], [77.7, 71.0], [77.8, 71.0], [77.9, 71.0], [78.0, 71.0], [78.1, 71.0], [78.2, 71.0], [78.3, 71.0], [78.4, 71.0], [78.5, 71.0], [78.6, 71.0], [78.7, 71.0], [78.8, 71.0], [78.9, 71.0], [79.0, 71.0], [79.1, 71.0], [79.2, 72.0], [79.3, 72.0], [79.4, 72.0], [79.5, 72.0], [79.6, 72.0], [79.7, 72.0], [79.8, 72.0], [79.9, 72.0], [80.0, 72.0], [80.1, 72.0], [80.2, 72.0], [80.3, 72.0], [80.4, 72.0], [80.5, 72.0], [80.6, 72.0], [80.7, 72.0], [80.8, 72.0], [80.9, 72.0], [81.0, 72.0], [81.1, 72.0], [81.2, 72.0], [81.3, 72.0], [81.4, 72.0], [81.5, 72.0], [81.6, 72.0], [81.7, 73.0], [81.8, 73.0], [81.9, 73.0], [82.0, 73.0], [82.1, 73.0], [82.2, 73.0], [82.3, 73.0], [82.4, 73.0], [82.5, 73.0], [82.6, 73.0], [82.7, 73.0], [82.8, 73.0], [82.9, 73.0], [83.0, 73.0], [83.1, 73.0], [83.2, 73.0], [83.3, 73.0], [83.4, 73.0], [83.5, 73.0], [83.6, 73.0], [83.7, 73.0], [83.8, 73.0], [83.9, 73.0], [84.0, 73.0], [84.1, 74.0], [84.2, 74.0], [84.3, 74.0], [84.4, 74.0], [84.5, 74.0], [84.6, 74.0], [84.7, 74.0], [84.8, 74.0], [84.9, 74.0], [85.0, 74.0], [85.1, 74.0], [85.2, 74.0], [85.3, 74.0], [85.4, 74.0], [85.5, 74.0], [85.6, 74.0], [85.7, 74.0], [85.8, 74.0], [85.9, 74.0], [86.0, 74.0], [86.1, 75.0], [86.2, 75.0], [86.3, 75.0], [86.4, 75.0], [86.5, 75.0], [86.6, 75.0], [86.7, 75.0], [86.8, 75.0], [86.9, 75.0], [87.0, 75.0], [87.1, 75.0], [87.2, 75.0], [87.3, 75.0], [87.4, 75.0], [87.5, 75.0], [87.6, 75.0], [87.7, 75.0], [87.8, 76.0], [87.9, 76.0], [88.0, 76.0], [88.1, 76.0], [88.2, 76.0], [88.3, 76.0], [88.4, 76.0], [88.5, 76.0], [88.6, 76.0], [88.7, 76.0], [88.8, 76.0], [88.9, 76.0], [89.0, 76.0], [89.1, 76.0], [89.2, 76.0], [89.3, 77.0], [89.4, 77.0], [89.5, 77.0], [89.6, 77.0], [89.7, 77.0], [89.8, 77.0], [89.9, 77.0], [90.0, 77.0], [90.1, 77.0], [90.2, 77.0], [90.3, 77.0], [90.4, 77.0], [90.5, 77.0], [90.6, 78.0], [90.7, 78.0], [90.8, 78.0], [90.9, 78.0], [91.0, 78.0], [91.1, 78.0], [91.2, 78.0], [91.3, 78.0], [91.4, 78.0], [91.5, 79.0], [91.6, 79.0], [91.7, 79.0], [91.8, 79.0], [91.9, 79.0], [92.0, 79.0], [92.1, 79.0], [92.2, 79.0], [92.3, 80.0], [92.4, 80.0], [92.5, 80.0], [92.6, 80.0], [92.7, 80.0], [92.8, 80.0], [92.9, 80.0], [93.0, 80.0], [93.1, 81.0], [93.2, 81.0], [93.3, 81.0], [93.4, 81.0], [93.5, 81.0], [93.6, 81.0], [93.7, 82.0], [93.8, 82.0], [93.9, 82.0], [94.0, 82.0], [94.1, 83.0], [94.2, 83.0], [94.3, 83.0], [94.4, 84.0], [94.5, 84.0], [94.6, 84.0], [94.7, 84.0], [94.8, 85.0], [94.9, 85.0], [95.0, 85.0], [95.1, 86.0], [95.2, 86.0], [95.3, 87.0], [95.4, 87.0], [95.5, 88.0], [95.6, 89.0], [95.7, 90.0], [95.8, 91.0], [95.9, 92.0], [96.0, 93.0], [96.1, 94.0], [96.2, 96.0], [96.3, 97.0], [96.4, 99.0], [96.5, 101.0], [96.6, 103.0], [96.7, 105.0], [96.8, 108.0], [96.9, 112.0], [97.0, 116.0], [97.1, 119.0], [97.2, 122.0], [97.3, 127.0], [97.4, 131.0], [97.5, 136.0], [97.6, 139.0], [97.7, 145.0], [97.8, 149.0], [97.9, 156.0], [98.0, 163.0], [98.1, 171.0], [98.2, 178.0], [98.3, 185.0], [98.4, 191.0], [98.5, 201.0], [98.6, 209.0], [98.7, 222.0], [98.8, 230.0], [98.9, 243.0], [99.0, 255.0], [99.1, 271.0], [99.2, 295.0], [99.3, 307.0], [99.4, 326.0], [99.5, 354.0], [99.6, 374.0], [99.7, 407.0], [99.8, 478.0], [99.9, 589.0], [100.0, 796.0]], "isOverall": false, "label": "GET /perfiles/{clienteId}", "isController": false}], "supportsControllersDiscrimination": true, "maxX": 100.0, "title": "Response Time Percentiles"}},
        getOptions: function() {
            return {
                series: {
                    points: { show: false }
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendResponseTimePercentiles'
                },
                xaxis: {
                    tickDecimals: 1,
                    axisLabel: "Percentiles",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Percentile value in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : %x.2 percentile was %y ms"
                },
                selection: { mode: "xy" },
            };
        },
        createGraph: function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesResponseTimePercentiles"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotResponseTimesPercentiles"), dataset, options);
            // setup overview
            $.plot($("#overviewResponseTimesPercentiles"), dataset, prepareOverviewOptions(options));
        }
};

/**
 * @param elementId Id of element where we display message
 */
function setEmptyGraph(elementId) {
    $(function() {
        $(elementId).text("No graph series with filter="+seriesFilter);
    });
}

// Response times percentiles
function refreshResponseTimePercentiles() {
    var infos = responseTimePercentilesInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyResponseTimePercentiles");
        return;
    }
    if (isGraph($("#flotResponseTimesPercentiles"))){
        infos.createGraph();
    } else {
        var choiceContainer = $("#choicesResponseTimePercentiles");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotResponseTimesPercentiles", "#overviewResponseTimesPercentiles");
        $('#bodyResponseTimePercentiles .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
}

var responseTimeDistributionInfos = {
        data: {"result": {"minY": 1.0, "minX": 0.0, "maxY": 14479.0, "series": [{"data": [[0.0, 14479.0], [300.0, 62.0], [600.0, 11.0], [700.0, 1.0], [400.0, 24.0], [200.0, 115.0], [100.0, 308.0], [500.0, 14.0]], "isOverall": false, "label": "GET /perfiles/{clienteId}", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 100, "maxX": 700.0, "title": "Response Time Distribution"}},
        getOptions: function() {
            var granularity = this.data.result.granularity;
            return {
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendResponseTimeDistribution'
                },
                xaxis:{
                    axisLabel: "Response times in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of responses",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                bars : {
                    show: true,
                    barWidth: this.data.result.granularity
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: function(label, xval, yval, flotItem){
                        return yval + " responses for " + label + " were between " + xval + " and " + (xval + granularity) + " ms";
                    }
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotResponseTimeDistribution"), prepareData(data.result.series, $("#choicesResponseTimeDistribution")), options);
        }

};

// Response time distribution
function refreshResponseTimeDistribution() {
    var infos = responseTimeDistributionInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyResponseTimeDistribution");
        return;
    }
    if (isGraph($("#flotResponseTimeDistribution"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesResponseTimeDistribution");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        $('#footerResponseTimeDistribution .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};


var syntheticResponseTimeDistributionInfos = {
        data: {"result": {"minY": 26.0, "minX": 0.0, "ticks": [[0, "Requests having \nresponse time <= 500ms"], [1, "Requests having \nresponse time > 500ms and <= 1,500ms"], [2, "Requests having \nresponse time > 1,500ms"], [3, "Requests in error"]], "maxY": 14988.0, "series": [{"data": [[0.0, 14988.0]], "color": "#9ACD32", "isOverall": false, "label": "Requests having \nresponse time <= 500ms", "isController": false}, {"data": [[1.0, 26.0]], "color": "yellow", "isOverall": false, "label": "Requests having \nresponse time > 500ms and <= 1,500ms", "isController": false}, {"data": [], "color": "orange", "isOverall": false, "label": "Requests having \nresponse time > 1,500ms", "isController": false}, {"data": [], "color": "#FF6347", "isOverall": false, "label": "Requests in error", "isController": false}], "supportsControllersDiscrimination": false, "maxX": 1.0, "title": "Synthetic Response Times Distribution"}},
        getOptions: function() {
            return {
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendSyntheticResponseTimeDistribution'
                },
                xaxis:{
                    axisLabel: "Response times ranges",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                    tickLength:0,
                    min:-0.5,
                    max:3.5
                },
                yaxis: {
                    axisLabel: "Number of responses",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                bars : {
                    show: true,
                    align: "center",
                    barWidth: 0.25,
                    fill:.75
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: function(label, xval, yval, flotItem){
                        return yval + " " + label;
                    }
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var options = this.getOptions();
            prepareOptions(options, data);
            options.xaxis.ticks = data.result.ticks;
            $.plot($("#flotSyntheticResponseTimeDistribution"), prepareData(data.result.series, $("#choicesSyntheticResponseTimeDistribution")), options);
        }

};

// Response time distribution
function refreshSyntheticResponseTimeDistribution() {
    var infos = syntheticResponseTimeDistributionInfos;
    prepareSeries(infos.data, true);
    if (isGraph($("#flotSyntheticResponseTimeDistribution"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesSyntheticResponseTimeDistribution");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        $('#footerSyntheticResponseTimeDistribution .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var activeThreadsOverTimeInfos = {
        data: {"result": {"minY": 16.740131578947373, "minX": 1.79450052E12, "maxY": 20.0, "series": [{"data": [[1.7945016E12, 20.0], [1.7945013E12, 20.0], [1.7945007E12, 20.0], [1.794501E12, 20.0], [1.79450202E12, 19.38064516129033], [1.79450172E12, 20.0], [1.79450142E12, 20.0], [1.79450178E12, 20.0], [1.79450118E12, 20.0], [1.79450148E12, 20.0], [1.79450058E12, 20.0], [1.79450088E12, 20.0], [1.7945019E12, 20.0], [1.79450064E12, 20.0], [1.79450196E12, 20.0], [1.79450166E12, 20.0], [1.79450106E12, 20.0], [1.79450136E12, 20.0], [1.79450076E12, 20.0], [1.79450082E12, 20.0], [1.79450112E12, 20.0], [1.79450052E12, 16.740131578947373], [1.79450184E12, 20.0], [1.79450154E12, 20.0], [1.79450094E12, 20.0], [1.79450124E12, 20.0]], "isOverall": false, "label": "Consultas de perfil (clientes vigentes)", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79450202E12, "title": "Active Threads Over Time"}},
        getOptions: function() {
            return {
                series: {
                    stack: true,
                    lines: {
                        show: true,
                        fill: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of active threads",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: {
                    noColumns: 6,
                    show: true,
                    container: '#legendActiveThreadsOverTime'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                selection: {
                    mode: 'xy'
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : At %x there were %y active threads"
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesActiveThreadsOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotActiveThreadsOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewActiveThreadsOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Active Threads Over Time
function refreshActiveThreadsOverTime(fixTimestamps) {
    var infos = activeThreadsOverTimeInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, 0);
    }
    if(isGraph($("#flotActiveThreadsOverTime"))) {
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesActiveThreadsOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotActiveThreadsOverTime", "#overviewActiveThreadsOverTime");
        $('#footerActiveThreadsOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var timeVsThreadsInfos = {
        data: {"result": {"minY": 56.0, "minX": 1.0, "maxY": 144.85714285714286, "series": [{"data": [[2.0, 144.85714285714286], [8.0, 70.375], [9.0, 60.333333333333336], [10.0, 69.4], [11.0, 66.25], [3.0, 73.71428571428571], [12.0, 65.8], [13.0, 60.8], [14.0, 68.44444444444444], [15.0, 73.2], [4.0, 69.83333333333334], [16.0, 74.83333333333333], [1.0, 56.0], [17.0, 65.60000000000001], [18.0, 69.5], [19.0, 58.166666666666664], [5.0, 66.33333333333334], [20.0, 69.06030893216925], [6.0, 77.0], [7.0, 67.87499999999999]], "isOverall": false, "label": "GET /perfiles/{clienteId}", "isController": false}, {"data": [[19.921206873584637, 69.0895830558147]], "isOverall": false, "label": "GET /perfiles/{clienteId}-Aggregated", "isController": false}], "supportsControllersDiscrimination": true, "maxX": 20.0, "title": "Time VS Threads"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    axisLabel: "Number of active threads",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Average response times in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: { noColumns: 2,show: true, container: '#legendTimeVsThreads' },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s: At %x.2 active threads, Average response time was %y.2 ms"
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesTimeVsThreads"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotTimesVsThreads"), dataset, options);
            // setup overview
            $.plot($("#overviewTimesVsThreads"), dataset, prepareOverviewOptions(options));
        }
};

// Time vs threads
function refreshTimeVsThreads(){
    var infos = timeVsThreadsInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyTimeVsThreads");
        return;
    }
    if(isGraph($("#flotTimesVsThreads"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesTimeVsThreads");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotTimesVsThreads", "#overviewTimesVsThreads");
        $('#footerTimeVsThreads .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var bytesThroughputOverTimeInfos = {
        data : {"result": {"minY": 1977.4, "minX": 1.79450052E12, "maxY": 4230.0, "series": [{"data": [[1.7945016E12, 3902.8], [1.7945013E12, 3902.8], [1.7945007E12, 3902.8], [1.794501E12, 3902.8], [1.79450202E12, 2016.4666666666667], [1.79450172E12, 3902.8], [1.79450142E12, 3902.8], [1.79450178E12, 3902.8], [1.79450118E12, 3902.8], [1.79450148E12, 3902.8], [1.79450058E12, 3902.8], [1.79450088E12, 3902.8], [1.7945019E12, 3902.8], [1.79450064E12, 3902.8], [1.79450196E12, 3902.8], [1.79450166E12, 3902.8], [1.79450106E12, 3902.8], [1.79450136E12, 3902.8], [1.79450076E12, 3902.8], [1.79450082E12, 3902.8], [1.79450112E12, 3902.8], [1.79450052E12, 1977.4], [1.79450184E12, 3902.8], [1.79450154E12, 3902.8], [1.79450094E12, 3902.8], [1.79450124E12, 3902.8]], "isOverall": false, "label": "Bytes received per second", "isController": false}, {"data": [[1.7945016E12, 4230.0], [1.7945013E12, 4230.0], [1.7945007E12, 4230.0], [1.794501E12, 4230.0], [1.79450202E12, 2185.5], [1.79450172E12, 4230.0], [1.79450142E12, 4230.0], [1.79450178E12, 4230.0], [1.79450118E12, 4230.0], [1.79450148E12, 4230.0], [1.79450058E12, 4230.0], [1.79450088E12, 4230.0], [1.7945019E12, 4230.0], [1.79450064E12, 4230.0], [1.79450196E12, 4230.0], [1.79450166E12, 4230.0], [1.79450106E12, 4230.0], [1.79450136E12, 4230.0], [1.79450076E12, 4230.0], [1.79450082E12, 4230.0], [1.79450112E12, 4230.0], [1.79450052E12, 2143.2], [1.79450184E12, 4230.0], [1.79450154E12, 4230.0], [1.79450094E12, 4230.0], [1.79450124E12, 4230.0]], "isOverall": false, "label": "Bytes sent per second", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79450202E12, "title": "Bytes Throughput Over Time"}},
        getOptions : function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity) ,
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Bytes / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendBytesThroughputOverTime'
                },
                selection: {
                    mode: "xy"
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s at %x was %y"
                }
            };
        },
        createGraph : function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesBytesThroughputOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotBytesThroughputOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewBytesThroughputOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Bytes throughput Over Time
function refreshBytesThroughputOverTime(fixTimestamps) {
    var infos = bytesThroughputOverTimeInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, 0);
    }
    if(isGraph($("#flotBytesThroughputOverTime"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesBytesThroughputOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotBytesThroughputOverTime", "#overviewBytesThroughputOverTime");
        $('#footerBytesThroughputOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
}

var responseTimesOverTimeInfos = {
        data: {"result": {"minY": 64.65166666666657, "minX": 1.79450052E12, "maxY": 78.72333333333327, "series": [{"data": [[1.7945016E12, 68.39333333333326], [1.7945013E12, 71.70666666666668], [1.7945007E12, 78.72333333333327], [1.794501E12, 75.42666666666663], [1.79450202E12, 70.90322580645166], [1.79450172E12, 66.08000000000006], [1.79450142E12, 64.72666666666666], [1.79450178E12, 67.91333333333331], [1.79450118E12, 68.87500000000007], [1.79450148E12, 67.01000000000005], [1.79450058E12, 71.34166666666663], [1.79450088E12, 70.07499999999993], [1.7945019E12, 65.89833333333327], [1.79450064E12, 70.11833333333333], [1.79450196E12, 68.00166666666674], [1.79450166E12, 64.97666666666653], [1.79450106E12, 66.46666666666664], [1.79450136E12, 65.89499999999991], [1.79450076E12, 71.77666666666649], [1.79450082E12, 70.55500000000008], [1.79450112E12, 66.55000000000001], [1.79450052E12, 66.57894736842107], [1.79450184E12, 64.65166666666657], [1.79450154E12, 68.11499999999995], [1.79450094E12, 77.12833333333322], [1.79450124E12, 68.07999999999998]], "isOverall": false, "label": "GET /perfiles/{clienteId}", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79450202E12, "title": "Response Time Over Time"}},
        getOptions: function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Average response time in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendResponseTimesOverTime'
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : at %x Average response time was %y ms"
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesResponseTimesOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotResponseTimesOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewResponseTimesOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Response Times Over Time
function refreshResponseTimeOverTime(fixTimestamps) {
    var infos = responseTimesOverTimeInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyResponseTimeOverTime");
        return;
    }
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, 0);
    }
    if(isGraph($("#flotResponseTimesOverTime"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesResponseTimesOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotResponseTimesOverTime", "#overviewResponseTimesOverTime");
        $('#footerResponseTimesOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var latenciesOverTimeInfos = {
        data: {"result": {"minY": 64.64499999999998, "minX": 1.79450052E12, "maxY": 78.70333333333325, "series": [{"data": [[1.7945016E12, 68.39166666666661], [1.7945013E12, 71.69666666666666], [1.7945007E12, 78.70333333333325], [1.794501E12, 75.42], [1.79450202E12, 70.8903225806451], [1.79450172E12, 66.07166666666669], [1.79450142E12, 64.72500000000002], [1.79450178E12, 67.91166666666668], [1.79450118E12, 68.87333333333336], [1.79450148E12, 67.00666666666667], [1.79450058E12, 71.32500000000003], [1.79450088E12, 70.06666666666672], [1.7945019E12, 65.89333333333329], [1.79450064E12, 70.10333333333338], [1.79450196E12, 68.0], [1.79450166E12, 64.97166666666669], [1.79450106E12, 66.46166666666669], [1.79450136E12, 65.89166666666657], [1.79450076E12, 71.76500000000001], [1.79450082E12, 70.54333333333336], [1.79450112E12, 66.54833333333333], [1.79450052E12, 66.52960526315798], [1.79450184E12, 64.64499999999998], [1.79450154E12, 68.11333333333326], [1.79450094E12, 77.11666666666666], [1.79450124E12, 68.07500000000007]], "isOverall": false, "label": "GET /perfiles/{clienteId}", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79450202E12, "title": "Latencies Over Time"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Average response latencies in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendLatenciesOverTime'
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : at %x Average latency was %y ms"
                }
            };
        },
        createGraph: function () {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesLatenciesOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotLatenciesOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewLatenciesOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Latencies Over Time
function refreshLatenciesOverTime(fixTimestamps) {
    var infos = latenciesOverTimeInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyLatenciesOverTime");
        return;
    }
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, 0);
    }
    if(isGraph($("#flotLatenciesOverTime"))) {
        infos.createGraph();
    }else {
        var choiceContainer = $("#choicesLatenciesOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotLatenciesOverTime", "#overviewLatenciesOverTime");
        $('#footerLatenciesOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var connectTimeOverTimeInfos = {
        data: {"result": {"minY": 0.13000000000000014, "minX": 1.79450052E12, "maxY": 2.35526315789474, "series": [{"data": [[1.7945016E12, 0.2833333333333333], [1.7945013E12, 0.17166666666666666], [1.7945007E12, 0.2666666666666664], [1.794501E12, 0.22666666666666663], [1.79450202E12, 0.22580645161290308], [1.79450172E12, 0.20666666666666678], [1.79450142E12, 0.15999999999999998], [1.79450178E12, 0.17666666666666664], [1.79450118E12, 0.16166666666666665], [1.79450148E12, 0.14166666666666672], [1.79450058E12, 0.3333333333333331], [1.79450088E12, 0.2233333333333333], [1.7945019E12, 0.1533333333333333], [1.79450064E12, 0.2916666666666672], [1.79450196E12, 0.13000000000000014], [1.79450166E12, 0.16833333333333333], [1.79450106E12, 0.1633333333333334], [1.79450136E12, 0.19499999999999995], [1.79450076E12, 0.22000000000000006], [1.79450082E12, 0.20500000000000013], [1.79450112E12, 0.15666666666666673], [1.79450052E12, 2.35526315789474], [1.79450184E12, 0.17500000000000016], [1.79450154E12, 0.18333333333333338], [1.79450094E12, 0.19000000000000003], [1.79450124E12, 0.2083333333333333]], "isOverall": false, "label": "GET /perfiles/{clienteId}", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79450202E12, "title": "Connect Time Over Time"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getConnectTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Average Connect Time in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendConnectTimeOverTime'
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : at %x Average connect time was %y ms"
                }
            };
        },
        createGraph: function () {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesConnectTimeOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotConnectTimeOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewConnectTimeOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Connect Time Over Time
function refreshConnectTimeOverTime(fixTimestamps) {
    var infos = connectTimeOverTimeInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyConnectTimeOverTime");
        return;
    }
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, 0);
    }
    if(isGraph($("#flotConnectTimeOverTime"))) {
        infos.createGraph();
    }else {
        var choiceContainer = $("#choicesConnectTimeOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotConnectTimeOverTime", "#overviewConnectTimeOverTime");
        $('#footerConnectTimeOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var responseTimePercentilesOverTimeInfos = {
        data: {"result": {"minY": 33.0, "minX": 1.79450052E12, "maxY": 796.0, "series": [{"data": [[1.7945016E12, 325.0], [1.7945013E12, 546.0], [1.7945007E12, 796.0], [1.794501E12, 545.0], [1.79450202E12, 306.0], [1.79450172E12, 295.0], [1.79450142E12, 234.0], [1.79450178E12, 348.0], [1.79450118E12, 454.0], [1.79450148E12, 261.0], [1.79450058E12, 478.0], [1.79450088E12, 489.0], [1.7945019E12, 183.0], [1.79450064E12, 440.0], [1.79450196E12, 296.0], [1.79450166E12, 191.0], [1.79450106E12, 307.0], [1.79450136E12, 223.0], [1.79450076E12, 405.0], [1.79450082E12, 406.0], [1.79450112E12, 207.0], [1.79450052E12, 459.0], [1.79450184E12, 226.0], [1.79450154E12, 424.0], [1.79450094E12, 694.0], [1.79450124E12, 343.0]], "isOverall": false, "label": "Max", "isController": false}, {"data": [[1.7945016E12, 80.0], [1.7945013E12, 77.0], [1.7945007E12, 77.0], [1.794501E12, 81.0], [1.79450202E12, 80.0], [1.79450172E12, 76.0], [1.79450142E12, 75.0], [1.79450178E12, 77.0], [1.79450118E12, 76.0], [1.79450148E12, 78.0], [1.79450058E12, 79.0], [1.79450088E12, 76.0], [1.7945019E12, 78.0], [1.79450064E12, 80.0], [1.79450196E12, 76.0], [1.79450166E12, 76.0], [1.79450106E12, 76.0], [1.79450136E12, 76.0], [1.79450076E12, 78.89999999999998], [1.79450082E12, 76.0], [1.79450112E12, 76.0], [1.79450052E12, 76.0], [1.79450184E12, 75.0], [1.79450154E12, 77.0], [1.79450094E12, 77.0], [1.79450124E12, 76.0]], "isOverall": false, "label": "90th percentile", "isController": false}, {"data": [[1.7945016E12, 241.5600000000004], [1.7945013E12, 383.82000000000016], [1.7945007E12, 620.94], [1.794501E12, 450.3300000000006], [1.79450202E12, 248.89999999999986], [1.79450172E12, 209.81000000000017], [1.79450142E12, 107.93000000000006], [1.79450178E12, 264.6800000000003], [1.79450118E12, 306.97], [1.79450148E12, 184.98000000000002], [1.79450058E12, 314.5300000000004], [1.79450088E12, 334.99], [1.7945019E12, 146.98000000000002], [1.79450064E12, 289.83000000000015], [1.79450196E12, 233.93000000000006], [1.79450166E12, 145.93000000000006], [1.79450106E12, 161.95000000000005], [1.79450136E12, 177.98000000000002], [1.79450076E12, 363.49000000000046], [1.79450082E12, 333.94000000000005], [1.79450112E12, 185.95000000000005], [1.79450052E12, 104.69999999999993], [1.79450184E12, 124.92000000000007], [1.79450154E12, 276.8000000000002], [1.79450094E12, 595.9300000000001], [1.79450124E12, 285.7700000000002]], "isOverall": false, "label": "99th percentile", "isController": false}, {"data": [[1.7945016E12, 93.94999999999993], [1.7945013E12, 85.94999999999993], [1.7945007E12, 93.0], [1.794501E12, 137.94999999999993], [1.79450202E12, 99.0], [1.79450172E12, 85.89999999999986], [1.79450142E12, 80.0], [1.79450178E12, 82.94999999999993], [1.79450118E12, 81.94999999999993], [1.79450148E12, 85.0], [1.79450058E12, 92.94999999999993], [1.79450088E12, 85.0], [1.7945019E12, 90.0], [1.79450064E12, 101.94999999999993], [1.79450196E12, 86.0], [1.79450166E12, 80.0], [1.79450106E12, 84.0], [1.79450136E12, 82.94999999999993], [1.79450076E12, 93.8499999999998], [1.79450082E12, 85.0], [1.79450112E12, 83.94999999999993], [1.79450052E12, 80.0], [1.79450184E12, 80.94999999999993], [1.79450154E12, 85.94999999999993], [1.79450094E12, 84.0], [1.79450124E12, 85.0]], "isOverall": false, "label": "95th percentile", "isController": false}, {"data": [[1.7945016E12, 40.0], [1.7945013E12, 34.0], [1.7945007E12, 36.0], [1.794501E12, 39.0], [1.79450202E12, 39.0], [1.79450172E12, 37.0], [1.79450142E12, 33.0], [1.79450178E12, 36.0], [1.79450118E12, 36.0], [1.79450148E12, 37.0], [1.79450058E12, 35.0], [1.79450088E12, 38.0], [1.7945019E12, 38.0], [1.79450064E12, 40.0], [1.79450196E12, 37.0], [1.79450166E12, 40.0], [1.79450106E12, 38.0], [1.79450136E12, 35.0], [1.79450076E12, 35.0], [1.79450082E12, 39.0], [1.79450112E12, 37.0], [1.79450052E12, 38.0], [1.79450184E12, 38.0], [1.79450154E12, 39.0], [1.79450094E12, 40.0], [1.79450124E12, 33.0]], "isOverall": false, "label": "Min", "isController": false}, {"data": [[1.7945016E12, 64.0], [1.7945013E12, 64.0], [1.7945007E12, 63.0], [1.794501E12, 64.0], [1.79450202E12, 67.0], [1.79450172E12, 62.0], [1.79450142E12, 64.0], [1.79450178E12, 63.0], [1.79450118E12, 63.0], [1.79450148E12, 64.0], [1.79450058E12, 64.0], [1.79450088E12, 63.5], [1.7945019E12, 63.0], [1.79450064E12, 64.0], [1.79450196E12, 64.0], [1.79450166E12, 63.0], [1.79450106E12, 64.0], [1.79450136E12, 63.0], [1.79450076E12, 64.0], [1.79450082E12, 64.0], [1.79450112E12, 63.0], [1.79450052E12, 65.0], [1.79450184E12, 63.0], [1.79450154E12, 63.0], [1.79450094E12, 63.0], [1.79450124E12, 63.0]], "isOverall": false, "label": "Median", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79450202E12, "title": "Response Time Percentiles Over Time (successful requests only)"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true,
                        fill: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Response Time in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendResponseTimePercentilesOverTime'
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : at %x Response time was %y ms"
                }
            };
        },
        createGraph: function () {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesResponseTimePercentilesOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotResponseTimePercentilesOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewResponseTimePercentilesOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Response Time Percentiles Over Time
function refreshResponseTimePercentilesOverTime(fixTimestamps) {
    var infos = responseTimePercentilesOverTimeInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, 0);
    }
    if(isGraph($("#flotResponseTimePercentilesOverTime"))) {
        infos.createGraph();
    }else {
        var choiceContainer = $("#choicesResponseTimePercentilesOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotResponseTimePercentilesOverTime", "#overviewResponseTimePercentilesOverTime");
        $('#footerResponseTimePercentilesOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};


var responseTimeVsRequestInfos = {
    data: {"result": {"minY": 63.0, "minX": 5.0, "maxY": 498.0, "series": [{"data": [[8.0, 298.5], [17.0, 498.0], [9.0, 91.0], [10.0, 63.0], [5.0, 70.0], [11.0, 145.0], [12.0, 80.5], [6.0, 321.0], [13.0, 70.0], [7.0, 188.0], [14.0, 240.5]], "isOverall": false, "label": "Successes", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 1000, "maxX": 17.0, "title": "Response Time Vs Request"}},
    getOptions: function() {
        return {
            series: {
                lines: {
                    show: false
                },
                points: {
                    show: true
                }
            },
            xaxis: {
                axisLabel: "Global number of requests per second",
                axisLabelUseCanvas: true,
                axisLabelFontSizePixels: 12,
                axisLabelFontFamily: 'Verdana, Arial',
                axisLabelPadding: 20,
            },
            yaxis: {
                axisLabel: "Median Response Time in ms",
                axisLabelUseCanvas: true,
                axisLabelFontSizePixels: 12,
                axisLabelFontFamily: 'Verdana, Arial',
                axisLabelPadding: 20,
            },
            legend: {
                noColumns: 2,
                show: true,
                container: '#legendResponseTimeVsRequest'
            },
            selection: {
                mode: 'xy'
            },
            grid: {
                hoverable: true // IMPORTANT! this is needed for tooltip to work
            },
            tooltip: true,
            tooltipOpts: {
                content: "%s : Median response time at %x req/s was %y ms"
            },
            colors: ["#9ACD32", "#FF6347"]
        };
    },
    createGraph: function () {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesResponseTimeVsRequest"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotResponseTimeVsRequest"), dataset, options);
        // setup overview
        $.plot($("#overviewResponseTimeVsRequest"), dataset, prepareOverviewOptions(options));

    }
};

// Response Time vs Request
function refreshResponseTimeVsRequest() {
    var infos = responseTimeVsRequestInfos;
    prepareSeries(infos.data);
    if (isGraph($("#flotResponseTimeVsRequest"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesResponseTimeVsRequest");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotResponseTimeVsRequest", "#overviewResponseTimeVsRequest");
        $('#footerResponseRimeVsRequest .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};


var latenciesVsRequestInfos = {
    data: {"result": {"minY": 63.0, "minX": 5.0, "maxY": 498.0, "series": [{"data": [[8.0, 298.5], [17.0, 498.0], [9.0, 91.0], [10.0, 63.0], [5.0, 70.0], [11.0, 145.0], [12.0, 80.5], [6.0, 321.0], [13.0, 70.0], [7.0, 188.0], [14.0, 240.5]], "isOverall": false, "label": "Successes", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 1000, "maxX": 17.0, "title": "Latencies Vs Request"}},
    getOptions: function() {
        return{
            series: {
                lines: {
                    show: false
                },
                points: {
                    show: true
                }
            },
            xaxis: {
                axisLabel: "Global number of requests per second",
                axisLabelUseCanvas: true,
                axisLabelFontSizePixels: 12,
                axisLabelFontFamily: 'Verdana, Arial',
                axisLabelPadding: 20,
            },
            yaxis: {
                axisLabel: "Median Latency in ms",
                axisLabelUseCanvas: true,
                axisLabelFontSizePixels: 12,
                axisLabelFontFamily: 'Verdana, Arial',
                axisLabelPadding: 20,
            },
            legend: { noColumns: 2,show: true, container: '#legendLatencyVsRequest' },
            selection: {
                mode: 'xy'
            },
            grid: {
                hoverable: true // IMPORTANT! this is needed for tooltip to work
            },
            tooltip: true,
            tooltipOpts: {
                content: "%s : Median Latency time at %x req/s was %y ms"
            },
            colors: ["#9ACD32", "#FF6347"]
        };
    },
    createGraph: function () {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesLatencyVsRequest"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotLatenciesVsRequest"), dataset, options);
        // setup overview
        $.plot($("#overviewLatenciesVsRequest"), dataset, prepareOverviewOptions(options));
    }
};

// Latencies vs Request
function refreshLatenciesVsRequest() {
        var infos = latenciesVsRequestInfos;
        prepareSeries(infos.data);
        if(isGraph($("#flotLatenciesVsRequest"))){
            infos.createGraph();
        }else{
            var choiceContainer = $("#choicesLatencyVsRequest");
            createLegend(choiceContainer, infos);
            infos.createGraph();
            setGraphZoomable("#flotLatenciesVsRequest", "#overviewLatenciesVsRequest");
            $('#footerLatenciesVsRequest .legendColorBox > div').each(function(i){
                $(this).clone().prependTo(choiceContainer.find("li").eq(i));
            });
        }
};

var hitsPerSecondInfos = {
        data: {"result": {"minY": 5.066666666666666, "minX": 1.79450052E12, "maxY": 10.0, "series": [{"data": [[1.7945016E12, 10.0], [1.7945013E12, 10.0], [1.7945007E12, 10.0], [1.794501E12, 10.0], [1.79450202E12, 5.166666666666667], [1.79450172E12, 10.0], [1.79450142E12, 10.0], [1.79450178E12, 10.0], [1.79450118E12, 10.0], [1.79450148E12, 10.0], [1.79450058E12, 10.0], [1.79450088E12, 10.0], [1.7945019E12, 10.0], [1.79450064E12, 10.0], [1.79450196E12, 10.0], [1.79450166E12, 10.0], [1.79450106E12, 10.0], [1.79450136E12, 10.0], [1.79450076E12, 10.0], [1.79450082E12, 10.0], [1.79450112E12, 10.0], [1.79450052E12, 5.066666666666666], [1.79450184E12, 10.0], [1.79450154E12, 10.0], [1.79450094E12, 10.0], [1.79450124E12, 10.0]], "isOverall": false, "label": "hitsPerSecond", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79450202E12, "title": "Hits Per Second"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of hits / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: "#legendHitsPerSecond"
                },
                selection: {
                    mode : 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s at %x was %y.2 hits/sec"
                }
            };
        },
        createGraph: function createGraph() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesHitsPerSecond"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotHitsPerSecond"), dataset, options);
            // setup overview
            $.plot($("#overviewHitsPerSecond"), dataset, prepareOverviewOptions(options));
        }
};

// Hits per second
function refreshHitsPerSecond(fixTimestamps) {
    var infos = hitsPerSecondInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, 0);
    }
    if (isGraph($("#flotHitsPerSecond"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesHitsPerSecond");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotHitsPerSecond", "#overviewHitsPerSecond");
        $('#footerHitsPerSecond .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
}

var codesPerSecondInfos = {
        data: {"result": {"minY": 5.066666666666666, "minX": 1.79450052E12, "maxY": 10.0, "series": [{"data": [[1.7945016E12, 10.0], [1.7945013E12, 10.0], [1.7945007E12, 10.0], [1.794501E12, 10.0], [1.79450202E12, 5.166666666666667], [1.79450172E12, 10.0], [1.79450142E12, 10.0], [1.79450178E12, 10.0], [1.79450118E12, 10.0], [1.79450148E12, 10.0], [1.79450058E12, 10.0], [1.79450088E12, 10.0], [1.7945019E12, 10.0], [1.79450064E12, 10.0], [1.79450196E12, 10.0], [1.79450166E12, 10.0], [1.79450106E12, 10.0], [1.79450136E12, 10.0], [1.79450076E12, 10.0], [1.79450082E12, 10.0], [1.79450112E12, 10.0], [1.79450052E12, 5.066666666666666], [1.79450184E12, 10.0], [1.79450154E12, 10.0], [1.79450094E12, 10.0], [1.79450124E12, 10.0]], "isOverall": false, "label": "200", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79450202E12, "title": "Codes Per Second"}},
        getOptions: function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of responses / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: "#legendCodesPerSecond"
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "Number of Response Codes %s at %x was %y.2 responses / sec"
                }
            };
        },
    createGraph: function() {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesCodesPerSecond"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotCodesPerSecond"), dataset, options);
        // setup overview
        $.plot($("#overviewCodesPerSecond"), dataset, prepareOverviewOptions(options));
    }
};

// Codes per second
function refreshCodesPerSecond(fixTimestamps) {
    var infos = codesPerSecondInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, 0);
    }
    if(isGraph($("#flotCodesPerSecond"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesCodesPerSecond");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotCodesPerSecond", "#overviewCodesPerSecond");
        $('#footerCodesPerSecond .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var transactionsPerSecondInfos = {
        data: {"result": {"minY": 5.066666666666666, "minX": 1.79450052E12, "maxY": 10.0, "series": [{"data": [[1.7945016E12, 10.0], [1.7945013E12, 10.0], [1.7945007E12, 10.0], [1.794501E12, 10.0], [1.79450202E12, 5.166666666666667], [1.79450172E12, 10.0], [1.79450142E12, 10.0], [1.79450178E12, 10.0], [1.79450118E12, 10.0], [1.79450148E12, 10.0], [1.79450058E12, 10.0], [1.79450088E12, 10.0], [1.7945019E12, 10.0], [1.79450064E12, 10.0], [1.79450196E12, 10.0], [1.79450166E12, 10.0], [1.79450106E12, 10.0], [1.79450136E12, 10.0], [1.79450076E12, 10.0], [1.79450082E12, 10.0], [1.79450112E12, 10.0], [1.79450052E12, 5.066666666666666], [1.79450184E12, 10.0], [1.79450154E12, 10.0], [1.79450094E12, 10.0], [1.79450124E12, 10.0]], "isOverall": false, "label": "GET /perfiles/{clienteId}-success", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79450202E12, "title": "Transactions Per Second"}},
        getOptions: function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of transactions / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: "#legendTransactionsPerSecond"
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s at %x was %y transactions / sec"
                }
            };
        },
    createGraph: function () {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesTransactionsPerSecond"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotTransactionsPerSecond"), dataset, options);
        // setup overview
        $.plot($("#overviewTransactionsPerSecond"), dataset, prepareOverviewOptions(options));
    }
};

// Transactions per second
function refreshTransactionsPerSecond(fixTimestamps) {
    var infos = transactionsPerSecondInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyTransactionsPerSecond");
        return;
    }
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, 0);
    }
    if(isGraph($("#flotTransactionsPerSecond"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesTransactionsPerSecond");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotTransactionsPerSecond", "#overviewTransactionsPerSecond");
        $('#footerTransactionsPerSecond .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var totalTPSInfos = {
        data: {"result": {"minY": 5.066666666666666, "minX": 1.79450052E12, "maxY": 10.0, "series": [{"data": [[1.7945016E12, 10.0], [1.7945013E12, 10.0], [1.7945007E12, 10.0], [1.794501E12, 10.0], [1.79450202E12, 5.166666666666667], [1.79450172E12, 10.0], [1.79450142E12, 10.0], [1.79450178E12, 10.0], [1.79450118E12, 10.0], [1.79450148E12, 10.0], [1.79450058E12, 10.0], [1.79450088E12, 10.0], [1.7945019E12, 10.0], [1.79450064E12, 10.0], [1.79450196E12, 10.0], [1.79450166E12, 10.0], [1.79450106E12, 10.0], [1.79450136E12, 10.0], [1.79450076E12, 10.0], [1.79450082E12, 10.0], [1.79450112E12, 10.0], [1.79450052E12, 5.066666666666666], [1.79450184E12, 10.0], [1.79450154E12, 10.0], [1.79450094E12, 10.0], [1.79450124E12, 10.0]], "isOverall": false, "label": "Transaction-success", "isController": false}, {"data": [], "isOverall": false, "label": "Transaction-failure", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79450202E12, "title": "Total Transactions Per Second"}},
        getOptions: function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of transactions / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: "#legendTotalTPS"
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s at %x was %y transactions / sec"
                },
                colors: ["#9ACD32", "#FF6347"]
            };
        },
    createGraph: function () {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesTotalTPS"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotTotalTPS"), dataset, options);
        // setup overview
        $.plot($("#overviewTotalTPS"), dataset, prepareOverviewOptions(options));
    }
};

// Total Transactions per second
function refreshTotalTPS(fixTimestamps) {
    var infos = totalTPSInfos;
    // We want to ignore seriesFilter
    prepareSeries(infos.data, false, true);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, 0);
    }
    if(isGraph($("#flotTotalTPS"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesTotalTPS");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotTotalTPS", "#overviewTotalTPS");
        $('#footerTotalTPS .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

// Collapse the graph matching the specified DOM element depending the collapsed
// status
function collapse(elem, collapsed){
    if(collapsed){
        $(elem).parent().find(".fa-chevron-up").removeClass("fa-chevron-up").addClass("fa-chevron-down");
    } else {
        $(elem).parent().find(".fa-chevron-down").removeClass("fa-chevron-down").addClass("fa-chevron-up");
        if (elem.id == "bodyBytesThroughputOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshBytesThroughputOverTime(true);
            }
            document.location.href="#bytesThroughputOverTime";
        } else if (elem.id == "bodyLatenciesOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshLatenciesOverTime(true);
            }
            document.location.href="#latenciesOverTime";
        } else if (elem.id == "bodyCustomGraph") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshCustomGraph(true);
            }
            document.location.href="#responseCustomGraph";
        } else if (elem.id == "bodyConnectTimeOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshConnectTimeOverTime(true);
            }
            document.location.href="#connectTimeOverTime";
        } else if (elem.id == "bodyResponseTimePercentilesOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshResponseTimePercentilesOverTime(true);
            }
            document.location.href="#responseTimePercentilesOverTime";
        } else if (elem.id == "bodyResponseTimeDistribution") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshResponseTimeDistribution();
            }
            document.location.href="#responseTimeDistribution" ;
        } else if (elem.id == "bodySyntheticResponseTimeDistribution") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshSyntheticResponseTimeDistribution();
            }
            document.location.href="#syntheticResponseTimeDistribution" ;
        } else if (elem.id == "bodyActiveThreadsOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshActiveThreadsOverTime(true);
            }
            document.location.href="#activeThreadsOverTime";
        } else if (elem.id == "bodyTimeVsThreads") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshTimeVsThreads();
            }
            document.location.href="#timeVsThreads" ;
        } else if (elem.id == "bodyCodesPerSecond") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshCodesPerSecond(true);
            }
            document.location.href="#codesPerSecond";
        } else if (elem.id == "bodyTransactionsPerSecond") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshTransactionsPerSecond(true);
            }
            document.location.href="#transactionsPerSecond";
        } else if (elem.id == "bodyTotalTPS") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshTotalTPS(true);
            }
            document.location.href="#totalTPS";
        } else if (elem.id == "bodyResponseTimeVsRequest") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshResponseTimeVsRequest();
            }
            document.location.href="#responseTimeVsRequest";
        } else if (elem.id == "bodyLatenciesVsRequest") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshLatenciesVsRequest();
            }
            document.location.href="#latencyVsRequest";
        }
    }
}

/*
 * Activates or deactivates all series of the specified graph (represented by id parameter)
 * depending on checked argument.
 */
function toggleAll(id, checked){
    var placeholder = document.getElementById(id);

    var cases = $(placeholder).find(':checkbox');
    cases.prop('checked', checked);
    $(cases).parent().children().children().toggleClass("legend-disabled", !checked);

    var choiceContainer;
    if ( id == "choicesBytesThroughputOverTime"){
        choiceContainer = $("#choicesBytesThroughputOverTime");
        refreshBytesThroughputOverTime(false);
    } else if(id == "choicesResponseTimesOverTime"){
        choiceContainer = $("#choicesResponseTimesOverTime");
        refreshResponseTimeOverTime(false);
    }else if(id == "choicesResponseCustomGraph"){
        choiceContainer = $("#choicesResponseCustomGraph");
        refreshCustomGraph(false);
    } else if ( id == "choicesLatenciesOverTime"){
        choiceContainer = $("#choicesLatenciesOverTime");
        refreshLatenciesOverTime(false);
    } else if ( id == "choicesConnectTimeOverTime"){
        choiceContainer = $("#choicesConnectTimeOverTime");
        refreshConnectTimeOverTime(false);
    } else if ( id == "choicesResponseTimePercentilesOverTime"){
        choiceContainer = $("#choicesResponseTimePercentilesOverTime");
        refreshResponseTimePercentilesOverTime(false);
    } else if ( id == "choicesResponseTimePercentiles"){
        choiceContainer = $("#choicesResponseTimePercentiles");
        refreshResponseTimePercentiles();
    } else if(id == "choicesActiveThreadsOverTime"){
        choiceContainer = $("#choicesActiveThreadsOverTime");
        refreshActiveThreadsOverTime(false);
    } else if ( id == "choicesTimeVsThreads"){
        choiceContainer = $("#choicesTimeVsThreads");
        refreshTimeVsThreads();
    } else if ( id == "choicesSyntheticResponseTimeDistribution"){
        choiceContainer = $("#choicesSyntheticResponseTimeDistribution");
        refreshSyntheticResponseTimeDistribution();
    } else if ( id == "choicesResponseTimeDistribution"){
        choiceContainer = $("#choicesResponseTimeDistribution");
        refreshResponseTimeDistribution();
    } else if ( id == "choicesHitsPerSecond"){
        choiceContainer = $("#choicesHitsPerSecond");
        refreshHitsPerSecond(false);
    } else if(id == "choicesCodesPerSecond"){
        choiceContainer = $("#choicesCodesPerSecond");
        refreshCodesPerSecond(false);
    } else if ( id == "choicesTransactionsPerSecond"){
        choiceContainer = $("#choicesTransactionsPerSecond");
        refreshTransactionsPerSecond(false);
    } else if ( id == "choicesTotalTPS"){
        choiceContainer = $("#choicesTotalTPS");
        refreshTotalTPS(false);
    } else if ( id == "choicesResponseTimeVsRequest"){
        choiceContainer = $("#choicesResponseTimeVsRequest");
        refreshResponseTimeVsRequest();
    } else if ( id == "choicesLatencyVsRequest"){
        choiceContainer = $("#choicesLatencyVsRequest");
        refreshLatenciesVsRequest();
    }
    var color = checked ? "black" : "#818181";
    if(choiceContainer != null) {
        choiceContainer.find("label").each(function(){
            this.style.color = color;
        });
    }
}

