// 네이버 지도 객체 생성 및 각종 지도 관련 로직
var map = new naver.maps.Map('map', {
  center: new naver.maps.LatLng(35.1796, 129.0756), // 부산 중심
  zoom: 12
});

// 여기에 마커, 이벤트 등 추가 JS 코드 작성