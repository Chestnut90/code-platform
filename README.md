# 코딩테스트 플랫폼 API with Numble

## Summary
---
Django와 Django Rest Framework를 이용하여 코딩테스트를 수행하는 backend api를 제공합니다.</br>
기간 : 2023.03.03 ~ 03.16 (2-weeks)</br>


## Author
---
Chestnut (cowzon90@gmail.com)


## Stack
---
- __django__ and __django-rest-framework__
- __redis__ as cache
- __celery__(message queue) with __rabbitmq__ (broker)
- __postgresql15__ with docker
</br>
</br>

## Installation
---
Poetry를 사용하여 dependencies를 설치합니다.
```
poetry install

poetry shell # venv 활성화

python manage.py runserver 
# python manage.py test
# visit http://localhost:8000/swagger

```
Docker를 통해 Redis 캐시 및 rabbitmq 브로커 환경 만들기.
```
# redis
docker pull redis # latest version 
docker run \
        --name [name] \
        -d \
        -p 6379:6379 \
        redis

# rabbitmq
docker pull rabbitmq # latest version
docker run \
        -d \
        --name [name] \
        -p 15672:15672 \
        -p 5672:5672 \
        rabbitmq
docker exec rabbitmq rabbitmq-plugins enable rabbitmq_management # access ui, http://localhost:15672

# postgresql
docker pull postgres # lastest, 15
docker run \
        -d \
        --name [name] \
        -e POSTGRES_USER=code_platform \
        -e POSTGRES_DB=code_platform \
        -e POSTGRES_PASSWORD=code_platform \
        -p 32771:5432 \
        -v $(pwd)/db2:/var/lib/postgresql/data \
        postgres


```


## APIs
---
| url | methods | descriptions |
|---|:---|:---|
| `/problems`| GET, POST | 문제들을 조회하고 추가할 수 있습니다.  |
| `/problems/categories`| GET | 문제의 카테고리를 조회합니다. |
| `/problems/recommendation`| GET | 문제를 추천합니다. |
| `/problems/<id>`| GET, PUT, PATCH, DELETE | id에 해당하는 문제를 조회, 수정, 삭제 할 수 있습니다. |
| `/problems/<id>/answer-commentary`| GET | 문제에 대한 정답 및 해설을 확인합니다.|
| `/problems/<id>/submission`| GET | 사용자가 문제에 대한 응시 정보를 확인 할 수 있습니다. |
| `/problems/<id>/solutions`| GET, POST | 사용자가 문제에 대한 답을 제출하고 결과를 처리합니다. 혹은 제출한 답을 조회 합니다. |
| `/problems/<id>/solutions/<soltuion_id>`| GET | 사용자가 제출한 문제의 답을 단일 조회합니다. |

## [DB ERD link](https://dbdiagram.io/d/6406db43296d97641d85f4fd)

## 테스트, 성능, 개선
---
테스트
- django model 에 대한 unittest.
- api 에 대한 unnittest 일부.
- 대부분 manual test를 수행하였다...

성능 및 개선
- 트래픽 혹은 데이터베이스가 큰 것을 조건을 강제하기 위해 ModelManager의 get, fiilter 에 대하여 sleep을 주고 캐시로 극복할 수 있었다.
- 캐시 활용에서 문제의 정답 및 해설이 자주 업데이트 되지 않는 점에 대하여 캐시 기간을 늘리고, 정합성을 보장하기 위해서 정답 및 해설에 대한 데이터가 변경되면 DB에 저장하고 cache에 Update하도록 하였다.
- problems 리스트 조회에 대하여 query string에 대한 Key를 구성하고 캐시에 저장하였으나, 문제 추가에 대한 캐시 업데이트 나 보관 방향 등 고려할 필요가 있다.
- settings.py에 'DEBUG_PROBLEM_QUERY_DELAY', 'DEBUG_PROBLEM_CHECK_DELAY' 에 seconds 단위 초를 설정하여 테스트 할 수 있다.
- solution 제출 시 message queue를 활용해 비동기 처리하고 간이 polling을 구현하여 request에 대한 결과 확인을 할 수 있도록 하였다.