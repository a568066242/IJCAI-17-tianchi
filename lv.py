#-*- coding=gbk -*-

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression



def isInvalid(value):
    """
    check value whether inValid or not
    :param value:
    :return: nan or 0 is invalid and return true ,otherwise
    """
    if np.isnan(value) or value == 0:
        return True
    else:
        return False

def score(predict,real):
    """
    ���⹫ʽ
    :param predict: Ԥ��ֵ
    :param real: ��ʵֵ
    :return: �÷�
    """
    print "predict:", predict
    print "real:", real
    score = 0
    for i in range(predict.shape[0]):
        score += (abs(predict[i]-real[i])/(predict[i]+real[i]))
    score /= predict.shape[0]
    return score

def predictOneShop(shop_feature_path):
    #���Իع�
    clf = LinearRegression()
    feature = pd.read_csv(shop_feature_path)

    #����һ����7���и��У���Ӧ�±�1��7
    pays = feature[["count","pay_day1","pay_day2","pay_day3","pay_day4","pay_day5","pay_day6","pay_day7"]]
    #�ܼ�����
    weekday=feature["weekday"]
    #����������
    same_day=feature["same_day"]


    n_sample = feature.shape[0]
    x = np.zeros((n_sample, 4))

    mean=feature["count"].mean()
    var=feature["count"].var()
    #����4���������ֱ������������ֵ�������������ֵ������ƽ��ֵ�����ܷ���
    for i in range(n_sample):
        day = weekday[i]
        last_pay = pays.ix[i][day] #���������ֵ
        x[i][0] = mean if isInvalid(last_pay)  else last_pay #��Ч���ɾ�ֵ���
        x[i][1] = mean if isInvalid(same_day[i]) else same_day[i] #�����������ֵ
        last_mean = pays.ix[i][1:8].mean() #������һ��ƽ��ֵ
        x[i][2] = mean if isInvalid(last_mean) else last_mean
        last_var = pays.ix[i][1:8].var()#������һ�ܷ���
        x[i][3] = var if isInvalid(last_var) else last_var

    train_x = x[:x.shape[0]-7]
    test_x = x[x.shape[0]-7:]
    train_y = feature["count"][:x.shape[0]-7]
    test_y = feature["count"][x.shape[0]-7:]
    # train_x = np.concatenate([train_x, train_x], axis = 0)
    # train_y = np.concatenate([train_y, train_y], axis = 0)
    clf.fit(train_x, train_y)
    return [clf.predict(test_x),test_y]

if __name__ == "__main__":
    predictAndReal = predictOneShop("data/feature/2trainset.csv")
    print score(predictAndReal[0], predictAndReal[1].values)
