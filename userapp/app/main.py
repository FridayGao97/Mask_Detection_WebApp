from flask import render_template, url_for
from app import webapp

import mysql.connector

import sys
from app import http


@webapp.route('/')
def main():
    http.record_requests()
    return render_template("main.html")