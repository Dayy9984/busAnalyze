let currentPolygon = null; // 현재 지도에 표시된 폴리곤(경계)
let map = null;

document.addEventListener('DOMContentLoaded', function() {
    // 1-1. 네이버 지도 객체 생성
    map = new naver.maps.Map('map', {
        center: new naver.maps.LatLng(35.1796, 129.0756), // 부산 중심 좌표
        zoom: 12
    });

    // 1-2. 검색 버튼 클릭 이벤트 등록 (id명 확인!)
    document.getElementById('searchBtn').addEventListener('click', function() {
        const address = document.getElementById('addressInput').value.trim();
        if (!address) {
            alert("검색어를 입력하세요.");
            return;
        }
        fetchCoordinates(address);
    });

    // 1-3. 검색창에서 엔터키 입력 이벤트 등록 (id명 확인!)
    document.getElementById('addressInput').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('searchBtn').click();
        }
    });
});

// 2. GET 요청으로 좌표/경계 데이터 받아오기
function fetchCoordinates(address) {
    fetch(`/backend/selected_coordinates?address=${encodeURIComponent(address)}`)
        .then(response => {
            if (!response.ok) throw new Error('검색 결과 없음');
            return response.json();
        })
        .then(data => {
            visualizeBoundary(data);
        })
        .catch(error => {
            alert('검색 결과가 없습니다.');
            console.error(error);
        });
}

// 3. 지도 중심 이동 및 폴리곤(경계) 시각화
function visualizeBoundary(data) {
    if (!data.coordinates || !data.multiPolygon || data.multiPolygon.length === 0) {
        alert("지도 데이터가 올바르지 않습니다.");
        return;
    }

    // 1. 지도 중심 이동 + zoom설정 (data.coordinates: [위도, 경도] 순서로 사용)
    map.setCenter(new naver.maps.LatLng(data.coordinates[0], data.coordinates[1]));
    map.setZoom(15);

    // 2. 기존 폴리곤 제거
    if (currentPolygon) {
        currentPolygon.setMap(null);
    }

    // 3. 다중 폴리곤 지원: 2중 map으로 paths 생성
    currentPolygon = new naver.maps.Polygon({
        map: map,
        paths: data.multiPolygon.map(
            polygon => polygon.map(pt => new naver.maps.LatLng(pt.lat, pt.lng))
        ),
        strokeColor: "#ff0000",
        strokeOpacity: 0.8,
        strokeWeight: 3,
        fillColor: "#ff0000",
        fillOpacity: 0.3
    });
}
