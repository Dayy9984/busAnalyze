let currentPolygon = null; // 행정동 경계 폴리곤 객체
let blindSpotPolygons = []; // 버스 사각지대 폴리곤 배열
let smartBusMarkers = [];   // 스마트버스정류장 마커 배열
let map = null;

const rankColors = {
    "1": "#2ecc71",  // 등급 1 - 초록
    "2": "#a3ba4a",  // 등급 2 - 연두
    "3": "#f1c40f",  // 등급 3 - 노랑
    "4": "#f39c12",  // 등급 4 - 주황
    "5": "#e74c3c"   // 등급 5 - 빨강
};

document.addEventListener('DOMContentLoaded', function() {
    map = new naver.maps.Map('map', {
        center: new naver.maps.LatLng(35.1796, 129.0756),
        zoom: 12
    });

    document.getElementById('modelSwitch').checked = false;

    // 최초 접속 시 부산 전체 사각지대 시각화
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

// ==================== [입지분석 시각화 핵심 부분] ====================
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
        // [입지분석] 검색 시 해당 지역의 스마트정류장 마커만 시각화
        fetch(`/backend/smart_bus?address=${encodeURIComponent(address)}`)
            .then(res => res.json())
            .then(data => visualizeSmartBus(data))
            .catch(() => alert('스마트버스정류장 데이터를 불러오지 못했습니다.'));
    }
}

function visualizeBlindSpot(data) {
    if (!data.BusBlindSpot || data.BusBlindSpot.length === 0) {
        alert("사각지대 데이터가 없습니다.");
        return;
    }
    data.BusBlindSpot.forEach(item => {
        if (item.polygon_coords) {
            const color = rankColors[item.rank] || "#999999";
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
    data.smartBus.forEach(station => {
        const marker = new naver.maps.Marker({
            position: new naver.maps.LatLng(station.lat, station.lon),
            map: map,
            title: station.station_name
        });
        smartBusMarkers.push(marker);
    });
}