import re

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/dashboard.html', 'r') as f:
    code = f.read()

# 1. Add Zone Toggles
zone_toggles = """
            <label style="cursor:pointer; color:#00e5ff; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-is" checked onchange="toggleLayers()"> IS</label>
            <label style="cursor:pointer; color:#2962ff; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-bos" checked onchange="toggleLayers()"> BOS</label>
            <label style="cursor:pointer; color:#e91e63; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-choch" checked onchange="toggleLayers()"> ChoCH</label>
            <span style="color:#363c4e;">|</span>
            <label style="cursor:pointer; color:#4caf50; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-demand" checked onchange="toggleLayers()"> Demand</label>
            <label style="cursor:pointer; color:#f44336; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-supply" checked onchange="toggleLayers()"> Supply</label>
"""
code = code.replace("""
            <label style="cursor:pointer; color:#00e5ff; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-is" checked onchange="toggleLayers()"> IS</label>
            <label style="cursor:pointer; color:#2962ff; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-bos" checked onchange="toggleLayers()"> BOS</label>
            <label style="cursor:pointer; color:#e91e63; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-choch" checked onchange="toggleLayers()"> ChoCH</label>""", zone_toggles)

# 2. Add zoneSeries array and rendering logic
zone_array_init = """
        let structureLines = [];
        let zoneSeries = [];
"""
code = code.replace("        let structureLines = [];", zone_array_init)

toggle_layers_additions = """
            const showDemand = document.getElementById('toggle-demand').checked;
            const showSupply = document.getElementById('toggle-supply').checked;

            pullbackLine.applyOptions({ visible: showPullback });

            // Clear old structure line series & zone series
            structureLines.forEach(l => {
                try { chart.removeSeries(l); } catch(e) {}
            });
            structureLines = [];
            
            zoneSeries.forEach(z => {
                try { chart.removeSeries(z); } catch(e) {}
            });
            zoneSeries = [];
"""
code = code.replace("""
            pullbackLine.applyOptions({ visible: showPullback });

            // Clear old structure line series
            structureLines.forEach(l => {
                try { chart.removeSeries(l); } catch(e) {}
            });
            structureLines = [];""", toggle_layers_additions)

zone_render_logic = """
                candleSeries.setMarkers(markers);
                
                // Draw Zones
                if (data.htf_zones && data.htf_zones.length > 0) {
                    // Limit zones to the last 200 to prevent WebGL crashing from thousands of series
                    const visibleZones = data.htf_zones.slice(-200);
                    
                    visibleZones.forEach(z => {
                        if (z.type === 'demand' && !showDemand) return;
                        if (z.type === 'supply' && !showSupply) return;
                        
                        const color = z.type === 'demand' ? 'rgba(76, 175, 80, 0.2)' : 'rgba(244, 67, 54, 0.2)';
                        const lineColor = z.type === 'demand' ? 'rgba(76, 175, 80, 0.5)' : 'rgba(244, 67, 54, 0.5)';
                        
                        const area = chart.addAreaSeries({
                            topColor: color,
                            bottomColor: color,
                            lineColor: lineColor,
                            lineWidth: 1,
                            lineStyle: LightweightCharts.LineStyle.Solid,
                            crosshairMarkerVisible: false,
                            lastValueVisible: false,
                            priceLineVisible: false,
                            lineType: LightweightCharts.LineType.Step,
                            baseValue: { type: 'price', price: z.type === 'demand' ? z.bottom : z.top }
                        });
                        
                        // We use the Step lineType. 
                        // Demand: baseValue = bottom, Line steps from high down.
                        // Supply: baseValue = top, Line steps from low up.
                        let areaData = [];
                        
                        // Sort history by time
                        z.history.sort((a,b) => a.time - b.time);
                        
                        z.history.forEach(h => {
                            areaData.push({
                                time: h.time, 
                                value: z.type === 'demand' ? h.top : h.bottom
                            });
                        });
                        
                        // Extend to end time
                        if (z.end_time) {
                            areaData.push({
                                time: z.end_time,
                                value: z.type === 'demand' ? areaData[areaData.length-1].value : areaData[areaData.length-1].value
                            });
                        }
                        
                        // Ensure unique times (sometimes history might have same day if bug)
                        const uniqueData = [];
                        const seenTimes = new Set();
                        areaData.forEach(d => {
                            if (!seenTimes.has(d.time)) {
                                seenTimes.add(d.time);
                                uniqueData.push(d);
                            }
                        });
                        
                        area.setData(uniqueData);
                        zoneSeries.push(area);
                    });
                }
            } else {
"""
code = code.replace("""
                candleSeries.setMarkers(markers);
            } else {""", zone_render_logic)

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/dashboard.html', 'w') as f:
    f.write(code)

