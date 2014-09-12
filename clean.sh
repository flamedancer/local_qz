#!/bin/bash
#coding: utf-8

# 把所有的tab \t 改成４个空格
find . -name \*.py -exec sed -i 's/\t/    /g' {} \;

# 把所有的(这是windows的\n)删除掉
find . -name \*.py -exec sed -i 's///g' {} \;

# 如果某行除了空格什么都没有的话，把空格删除掉
find . -name \*.py -exec sed -i 's/^\s*$//g' {} \;

# 把每一行的尾端的空格或tab \t删除掉
find . -name \*.py -exec sed -i 's/[ \t]*$//g' {} \;
