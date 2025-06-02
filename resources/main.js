let currentPolygon = null;
let blindSpotPolygons = [];
let smartBusMarkers = [];

const rankColors = {
    "1": "#e74c3c",
    "2": "#f39c12",
    "3": "#f1c40f",
    "4": "#a3ba4a",
    "5": "#2ecc71"
};

document.addEventListener('DOMContentLoaded', function() {
    map = new naver.maps.Map('map', {
        center: new naver.maps.LatLng(35.1796, 129.0756),
        zoom: 12
    });

    document.getElementById('modelSwitch').checked = false;

    if (!document.getElementById('modelSwitch').checked) {
        showBusanBlindSpots();
    }

    document.getElementById('searchBtn').addEventListener('click', function() {
        const address = document.getElementById('addressInput').value.trim();
        if (!address) {
            alert("검색어를 입력하세요.");
            return;
        }
        fetchCoordinates(address);
        fetchAndVisualizeExtra(address);
    });

    document.getElementById('addressInput').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('searchBtn').click();
        }
    });

    document.getElementById('modelSwitch').addEventListener('change', function() {
        resetAll();
        if (!this.checked) {
            showBusanBlindSpots();
        }
    });

    // 등급 선택 시 자동으로 다시 시각화
    document.getElementById('gradeSelect').addEventListener('change', function() {
        const address = document.getElementById('addressInput').value.trim();
        if (address) {
            fetchAndVisualizeExtra(address);
        } else if (!document.getElementById('modelSwitch').checked) {
            showBusanBlindSpots();
        }
    });

    resetAll();
});

function showBusanBlindSpots() {
    fetch('/backend/bus_blind_spot?address=부산광역시')
        .then(res => res.json())
        .then(data => visualizeBlindSpot(data))
        .catch(() => alert('부산 전체 사각지대 데이터를 불러오지 못했습니다.'));
}

function fetchCoordinates(address) {
    fetch(`/backend/selected_coordinates?address=${encodeURIComponent(address)}`)
        .then(res => res.json())
        .then(data => visualizeBoundary(data))
        .catch(() => alert('지도 경계 데이터를 불러오지 못했습니다.'));
}

function visualizeBoundary(data) {
    if (!data.coordinates || !data.multiPolygon || data.multiPolygon.length === 0) {
        alert("지도 데이터가 올바르지 않습니다.");
        return;
    }
    if (currentPolygon) currentPolygon.setMap(null);

    map.setCenter(new naver.maps.LatLng(data.coordinates[0], data.coordinates[1]));
    map.setZoom(15);

    currentPolygon = new naver.maps.Polygon({
        map: map,
        paths: data.multiPolygon.map(polygon => polygon.map(pt => new naver.maps.LatLng(pt.lat, pt.lng))),
        strokeColor: "#ff0000",
        strokeOpacity: 0.8,
        strokeWeight: 3,
        fillColor: "transparent",
        fillOpacity: 0
    });
}

function resetAll() {
    if (currentPolygon) {
        currentPolygon.setMap(null);
        currentPolygon = null;
    }
    blindSpotPolygons.forEach(p => p.setMap(null));
    blindSpotPolygons = [];
    smartBusMarkers.forEach(m => m.setMap(null));
    smartBusMarkers = [];
    map.setCenter(new naver.maps.LatLng(35.1796, 129.0756));
    map.setZoom(12);
    document.getElementById('addressInput').value = '';
    document.getElementById('autoComplete').innerHTML = '';
    document.getElementById('gradeSelect').value = '';
}

function fetchAndVisualizeExtra(address) {
    blindSpotPolygons.forEach(p => p.setMap(null));
    blindSpotPolygons = [];
    smartBusMarkers.forEach(m => m.setMap(null));
    smartBusMarkers = [];

    const isBlindSpot = !document.getElementById('modelSwitch').checked;

    if (isBlindSpot) {
        fetch(`/backend/bus_blind_spot?address=${encodeURIComponent(address)}`)
            .then(res => res.json())
            .then(data => visualizeBlindSpot(data))
            .catch(() => alert('사각지대 데이터를 불러오지 못했습니다.'));
    } else {
        fetch(`/backend/smart_bus?address=${encodeURIComponent(address)}`)
            .then(res => res.json())
            .then(data => visualizeSmartBus(data))
            .catch(() => alert('스마트버스정류장 데이터를 불러오지 못했습니다.'));
    }
}

function visualizeBlindSpot(data) {
    // 기존 폴리곤 모두 지도에서 제거
    blindSpotPolygons.forEach(p => p.setMap(null));
    blindSpotPolygons = [];

    if (!data.BusBlindSpot || data.BusBlindSpot.length === 0) {
        alert("사각지대 데이터가 없습니다.");
        return;
    }

    const selectedRank = document.getElementById('gradeSelect').value;
    const filtered = selectedRank
        ? data.BusBlindSpot.filter(item => String(item.rank) === String(selectedRank))
        : data.BusBlindSpot;

    filtered.forEach(item => {
        if (item.polygon_coords) {
            const color = rankColors[String(item.rank)] || "#999999";
            item.polygon_coords.forEach(polyArr => {
                const polygon = new naver.maps.Polygon({
                    map: map,
                    paths: polyArr.map(pt => new naver.maps.LatLng(pt.lat, pt.lng)),
                    strokeColor: color,
                    strokeOpacity: 0.8,
                    strokeWeight: 2,
                    fillColor: color,
                    fillOpacity: 0.3
                });
                blindSpotPolygons.push(polygon);
            });
        }
    });
}


function visualizeSmartBus(data) {
    if (!data.smartBus || data.smartBus.length === 0) {
        alert("스마트버스정류장 데이터가 없습니다.");
        return;
    }

    const selectedRank = document.getElementById('gradeSelect').value;
    const filtered = selectedRank
        ? data.smartBus.filter(station => String(station.rank) === String(selectedRank))
        : data.smartBus;

    filtered.forEach(station => {
        const color = rankColors[String(station.rank)] || "#999999";
        const marker = new naver.maps.Marker({
            position: new naver.maps.LatLng(station.lat, station.lon),
            map: map,
            icon: {
                content: `
                    <div style="
                        background: ${color};
                        width: 15px;
                        height: 15px;
                        border-radius: 50%;
                        border: 2.0px solid #fff;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.18);
                    "></div>
                `,
                size: new naver.maps.Size(15, 15),
                anchor: new naver.maps.Point(11, 11)
            },
            title: station.station_name
        });
        smartBusMarkers.push(marker);

        const infoContent = `
            <div style="padding:10px 15px;min-width:200px;background:#fff;border-radius:8px;">
                <h3 style="margin:0 0 8px;font-size:16px;color:#333;">${station.station_name}</h3>
                <div style="margin:5px 0;font-size:14px;color:#555;">
                    <strong>버스노선:</strong> ${station.line_num}
                </div>
                <div style="margin:5px 0;font-size:14px;color:#555;">
                    <strong>ARS번호:</strong> ${station.arsno}
                </div>
                <div style="margin:5px 0;font-size:14px;color:#555;">
                    <strong>입지등급:</strong> <span style="color:${color};font-weight:bold;">${station.rank}</span>
                </div>
            </div>
        `;
        const infoWindow = new naver.maps.InfoWindow({
            content: infoContent,
            maxWidth: 250,
            backgroundColor: "#fff",
            borderColor: "#ddd",
            borderWidth: 1,
            anchorSize: new naver.maps.Size(10, 10),
            anchorSkew: true,
            pixelOffset: new naver.maps.Point(0, -5)
        });

        naver.maps.Event.addListener(marker, "click", function() {
            smartBusMarkers.forEach(m => {
                if (m._infowindow && m._infowindow.getMap()) {
                    m._infowindow.close();
                }
            });
            if (infoWindow.getMap()) {
                infoWindow.close();
            } else {
                infoWindow.open(map, marker);
            }
            marker._infowindow = infoWindow;
        });
    });
}
