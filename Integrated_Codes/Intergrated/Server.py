from flask import Flask
from flask import render_template
from flask import request

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

from bson import ObjectId 
from datetime import datetime

import pymongo
from urllib import parse

import plotly.graph_objects as go

from query import *


class TextForm(FlaskForm):
    content = StringField('내용', validators=[DataRequired()])
    
#Config setting
app = Flask(__name__)
    
def conn():
    host="localhost"
    port="27017"
    user="user1"
    pwd="user1"
    db="TeamProject"
    
    client=pymongo.MongoClient("mongodb://{}:".format(user)
                               +parse.quote(pwd)
                               +"@{}:{}/{}".format(host,port,db))
    
    db_conn=client.get_database(db)
    
    collection1=db_conn.get_collection("Birth")
    collection2=db_conn.get_collection("Death")
    
    pipeline = MainPageQuery()
    
    result1=collection1.aggregate(pipeline)
    result2=collection2.aggregate(pipeline)
    
    return result1, result2

def conn2(case, region, keyword):
    host="localhost"
    port="27017"
    user="user1"
    pwd="user1"
    db="TeamProject"
    
    client=pymongo.MongoClient("mongodb://{}:".format(user)
                               +parse.quote(pwd)
                               +"@{}:{}/{}".format(host,port,db))
    
    db_conn=client.get_database(db)
    
    collection=db_conn.get_collection("Birth")
    
    #쿼리 불러오기
    pipeline = return_query(case, region, keyword)

    #쿼리 실행
    results = collection.aggregate(pipeline)

    #일반 케이스
    if case != 3:
        return results
    
    #리스트 리턴
    elif case == 3:
        list = []
        for d in results:
            date = (d["_id"]["년도"] +'.'+ d["_id"]["월"])
            region = (d["_id"]["읍면"])
            total = d["건수"]
            temp = {
                "date" : date,
                "region" : region,
                "total" : total
            }
            list.append(temp)
        
        return list

@app.route("/region", methods=['GET'])
def region_graph():
    region = request.args.get('region')   #지역
    keyword = request.args.get('search')  #세부지역

    #지역 검색(상세 시도군 설정X)
    if keyword is None or keyword.strip() == "":
        #각 쿼리 실행
        results = list(conn2(1, region, keyword))       #리스트 형태로 변화(안하면 에러)
        list_results = conn2(3, region, keyword)
        max_year = region_search_max_year(region)
        list_results_region_sort = region_sort_max_year(region)
        
        #막대그래프 그리기
        men_data = [d['건수'] for d in results if d['성별'] == '남자']
        women_data = [d['건수'] for d in results if d['성별']== '여자']
        year = sorted(set([d['년도'] for d in results]))
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=year, y=men_data, name='남자', marker_color='skyblue'))
        fig.add_trace(go.Bar(x=year, y=women_data, name='여자', marker_color='rgba(255, 192, 203, 1)'))

        fig.update_layout(
            title=region + ' ' +'년도별 남녀 출생 데이터',
            xaxis_title='년도',
            yaxis_title='건수',
            barmode='group'
        )

        graph = fig.to_html(full_html=False)

        #파이차트 그리기
        total_values = [item['total'] for item in list_results_region_sort]
        region_dates = [f"{item['region']} - {item['date']}" for item in list_results_region_sort]
        
        total_sum = sum(total_values)
        percentages = [(value / total_sum) * 100 for value in total_values]

        fig2 = go.Figure(data=[go.Pie(labels=region_dates, values=percentages)])
        fig2.update_layout(title= max_year + "년도 " + region + "지역 상위 6개 데이터")
        
        pie = fig2.to_html(full_html=False)

        return render_template('region_graph.html', graph=graph, results = list_results, pie = pie)
    
    #지역 상세 검색
    else :
        results = list(conn2(2, region, keyword))       #리스트 형태로 변화(안하면 에러)

        men_data = [d['건수'] for d in results if d['성별'] == '남자']
        women_data = [d['건수'] for d in results if d['성별']== '여자']
        year = sorted(set([d['년도'] for d in results]))
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=year, y=men_data, name='남자', marker_color='skyblue'))
        fig.add_trace(go.Bar(x=year, y=women_data, name='여자', marker_color='rgba(255, 192, 203, 1)'))

        fig.update_layout(
            title=region + ' ' + keyword + ' ' +'년도별 남녀 출생 데이터',
            xaxis_title='년도',
            yaxis_title='건수',
            barmode='group'
        )

        #graph = fig.to_html(full_html=False, default_height=500, default_width=700)
        graph = fig.to_html(full_html=False)

        return render_template('region_graph.html', graph=graph)
    
@app.route('/regionSearch')
def region_search():
    return render_template('region_search.html')

@app.route("/")
def home_page():
    # 데이터 초기화
    x_data1 = []
    y_data1 = []

    x_data2 = []
    y_data2 = []

    result1, result2 = conn()

    # 쿼리 결과를 이용하여 데이터 추출
    for data in result1:
        x_data1.append(data['_id'])
        y_data1.append(data['발생건수'])

    for data in result2:
        x_data2.append(data['_id'])
        y_data2.append(data['발생건수'])

    # 그래프 생성
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_data1, y=y_data1, mode='lines', name='출생'))
    fig.add_trace(go.Scatter(x=x_data2, y=y_data2, mode='lines', name='사망'))

    # 그래프 레이아웃 설정
    fig.update_layout(
        title='발생건수 그래프',
        xaxis_title='조회기간',
        yaxis_title='발생건수'
    )

    # 그래프를 HTML로 렌더링하여 반환
    chart = fig.to_html(full_html=False)
    
    return render_template('Main.html', chart=chart)

app.run()
