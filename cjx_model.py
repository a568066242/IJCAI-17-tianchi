#-*- coding=gbk -*-
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import  Lasso
from sklearn.linear_model import LassoCV

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
    # print "predict:", predict
    # print "real:", real
    score = 0
    for i in range(predict.shape[0]):
        score += (abs(predict[i]-real[i])/(predict[i]+real[i]))
    score /= predict.shape[0]
    return score


def toInt(x):
    """
    ��ndarray�е�������������
    :param x:
    :return:
    """
    for i in range(x.shape[0]):
        x[i] = int(round(x[i]))
    return x


def predictOneShopInTrain_Lasso(shop_feature_path, feature_size):
    """
    ����ģ��Ԥ�ⵥ���̵�
    ��ѵ�����Ǻ�14��Ϊѵ������Ԥ���14���ֵ
    :param shop_feature_path:
    :param feature_size:
    :return:
    """
    #���Իع�
    # clf = LinearRegression()
    feature = pd.read_csv(shop_feature_path)

    #����һ����7���и��У���Ӧ�±�1��7
    pays = feature[["count","pay_day1","pay_day2","pay_day3","pay_day4","pay_day5","pay_day6","pay_day7"]]
    #�ܼ�����
    weekday=feature["weekday"]
    #����������
    same_day=feature["same_day"]
    n_sample = feature.shape[0]
    x = np.zeros((n_sample, feature_size))

    mean=feature["count"].mean()
    std=feature["count"].std()
    #����4���������ֱ������������ֵ�������������ֵ������ƽ��ֵ�����ܷ���
    for i in range(n_sample):
        day = weekday[i]
        last_pay = pays.ix[i][day] #���������ֵ
        if feature_size >= 2:
            x[i][0] = mean if isInvalid(last_pay)  else last_pay #��Ч���ɾ�ֵ���
            x[i][1] = mean if isInvalid(same_day[i]) else same_day[i] #�����������ֵ
        if feature_size == 4:
            last_mean = pays.ix[i][1:8].mean() #������һ��ƽ��ֵ
            x[i][2] = mean if isInvalid(last_mean) else last_mean
            last_std = pays.ix[i][1:8].std()#������һ�ܷ���
            x[i][3] = std if isInvalid(last_std) else last_std

    train_x = x[:x.shape[0]-14]
    test_x = x[x.shape[0]-14:]
    train_y = feature["count"][:x.shape[0]-14]
    test_y = feature["count"][x.shape[0]-14:]
    scaler = StandardScaler()
    train_x = scaler.fit_transform(train_x)
    lassocv = LassoCV()
    lassocv.fit(train_x, train_y)
    lasso = Lasso(alpha=lassocv.alpha_)
    lasso.fit(train_x, train_y)

    # print "Lasso model: ", lasso.coef_
    # clf.fit(train_x, train_y)
    return [lasso.predict(test_x),test_y]


def predict_all_in_train_Lasso(version, feature_size):
    """
    ����ģ��Ԥ�������̵�
    ��ѵ�����Ǻ�14��Ϊѵ������Ԥ���14���ֵ
    :param version:
    :param feature_size:
    :return:
    """
    food_path="food_csvfile_holiday" + str(version)
    other_path = "other_csvfile_holiday" + str(version)
    market_path = "supermarket_csvfile_holiday" + str(version)
    paths = [food_path,other_path,market_path]
    import os
    real = None
    predict = None
    for path in paths:
        csvfiles = os.listdir(path)
        for filename in csvfiles:
            predictAndReal = predictOneShopInTrain_Lasso(path + "/" + filename, feature_size)
            if real is None:
                real = predictAndReal[1].values
            else:
                real = np.insert(real,len(real),predictAndReal[1].values)
            if predict is None:
                predict = predictAndReal[0]
            else:
                predict = np.insert(predict,len(predict),predictAndReal[0])
    return [predict, real]



if __name__ == "__main__":
    # prediceAndReal=predict_all(version=2,feature_size=4,save_filename="result/result_revise_f4.csv")
    # print predictOneShop("food_csvfile2/1243_trainset.csv",feature_size=4)
    prediceAndReal = predict_all_in_train_Lasso(version=2, feature_size=4)
    print score(prediceAndReal[0], prediceAndReal[1])