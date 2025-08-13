import math
def haversine(map_y1, map_x1, map_y2, map_x2):
    """
    두 지점의 위도와 경도 정보가 주어질 때 두 지점 사이의 거리를 구하는 함수입니다.
    :param map_x1: 경도 좌표 1
    :param map_y1: 위도 좌표 1
    :param map_x2: 경도 좌표 2
    :param map_y2: 위도 좌표 2
    """

    R = 6378  # 지구 반지름 (단위: km)

    # 위도 및 경도를 라디안 단위로 변환
    map_x1, map_y1, map_x2, map_y2 = map(math.radians, [map_x1, map_y1, map_x2, map_y2])

    # 위도, 경도의 차이 계산
    d_y = map_y2 - map_y1
    d_x = map_x2 - map_x1

    # haversine 공식 적용
    a = math.sin(d_y / 2) ** 2 + math.cos(map_y1) * math.cos(map_y2) * math.sin(d_x / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c  # 거리 계산
    return distance