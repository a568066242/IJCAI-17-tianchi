#encoding=utf-8


import datetime
from keras.wrappers.scikit_learn import KerasRegressor
from keras.optimizers import SGD,Adadelta,Adagrad,Adam,Adamax,Nadam
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression,Ridge,RidgeCV
from sklearn.preprocessing import MinMaxScaler,OneHotEncoder
from FeatureExtractor import *
from cjx_predict import scoreoneshop
from lv import removeNegetive,toInt
import numpy as np
from keras.layers import Dense
from keras.layers import SimpleRNN
from keras.models import Sequential
from keras.utils import np_utils
import Parameter
import pandas as pd
from cjx_predict import getCoutList
from cjx_predict import preprocessCoutList
from keras.optimizers import RMSprop
from keras.regularizers import l2, activity_l2,l1
from keras import backend as K
from keras.layers import LSTM
from lv import toInt,removeNegetive
from sklearn.preprocessing import MinMaxScaler
import datetime
from cjx_predict import scoreoneshop, score


def predictAllShop_ANN_part_together(all_data, trainAsTest=False, saveFilePath = None, featurePath = None, cate_level = 0, cate_name = None, featureSavePath = None, needSaveFeature = False, time = 1):
    """
    使用所有商家所有数据训练,预测所有商店
    :param trainAsTest: 是否使用训练集后14天作为测试集
    :param model: 某个模型
    :param saveFilePath
    :param featurePath:
    :param cate_level:
    :param cate_name:
    :param featureSavePath:
    :param needSaveFeature:
    :param time:跑第几次
    :return:
    """


    ignores = 0


    shopids = None
    shop_need_to_predict = 2000
    if(cate_level is 0):
        shopids = range(1, 1+shop_need_to_predict, 1)
    else:
        shopids = Parameter.extractShopValueByCate(cate_level,cate_name)

    shop_info = pd.read_csv(Parameter.shopinfopath,names=["shopid","cityname","locationid","perpay","score","comment","level","cate1","cate2","cate3"])
    weekOrWeekend = True
    day_back_num = 21
    sameday_backNum = 7
    week_backnum = 3
    other_features = [statistic_functon_mean,statistic_functon_median]
    other_features = []
    '''将cate1 onehot'''
    cate = shop_info['cate1'].tolist()
    cate_dup = set(cate)
    cates = []
    for i in range(len(cate_dup)):
        cates.append([i])
    hot_encoder = OneHotEncoder().fit(cates)
    dicts = dict(zip(cate_dup, range(len(cate_dup))))
    cate_num = []
    for c in cate:
        cate_num.append([dicts[c]])
    '''cate1 onehot finish'''



    if featurePath is None:

        all_x = None
        all_y = None
        for shopid in shopids:
            if shopid in Parameter.ignore_shopids:
                print "ignore get train", shopid
                ignores += 1
                continue
            print "get ", shopid, " train"
            part_data = all_data[all_data.shopid == shopid]
            last_14_real_y = None
            # 取出一部分做训练集
            if trainAsTest: #使用训练集后14天作为测试集的话，训练集为前面部分
                last_14_real_y = part_data[len(part_data) - 14:]["count"].values
                part_data = part_data[0:len(part_data) - 14]
            # print last_14_real_y
            skipNum = part_data.shape[0] - 128
            if skipNum < 0:
                skipNum = 0
            train_x = None
            if sameday_backNum != 0:
                sameday = extractBackSameday(part_data, sameday_backNum, skipNum, nan_method_sameday_mean)
                train_x = getOneWeekdayFomExtractedData(sameday)
            if day_back_num != 0:
                if train_x is not None:
                    train_x = np.concatenate((train_x, getOneWeekdayFomExtractedData(extractBackDay(part_data, day_back_num, skipNum, nan_method_sameday_mean))),axis=1)
                else:
                    train_x = getOneWeekdayFomExtractedData(extractBackDay(part_data, day_back_num, skipNum, nan_method_sameday_mean))
            if weekOrWeekend:
                ws = getOneWeekdayFomExtractedData(extractWorkOrWeekend(part_data,skipNum))
                hot_encoder = onehot(ws)
                train_x = np.concatenate((train_x, hot_encoder.transform(ws).toarray()), axis=1)
            count = extractCount(part_data, skipNum)
            train_y = getOneWeekdayFomExtractedData(count)
            for feature in other_features:
                value = getOneWeekdayFomExtractedData(extractBackWeekValue(part_data, week_backnum, skipNum, nan_method_sameday_mean, feature))
                train_x = np.append(train_x, value, axis=1)

            # '''添加商家信息'''
            # # print train_x,train_x.shape
            # index = shopid - 1
            # oneshopinfo = shop_info.ix[index]
            # shop_perpay = oneshopinfo['perpay'] if not pd.isnull(oneshopinfo['perpay']) else 0
            # shop_score = oneshopinfo['score'] if not pd.isnull(oneshopinfo['score']) else 0
            # shop_comment = oneshopinfo['comment'] if not pd.isnull(oneshopinfo['comment']) else 0
            # shop_level = oneshopinfo['level'] if not pd.isnull(oneshopinfo['level']) else 0
            # shop_cate1 = oneshopinfo['cate1']
            # import warnings
            # with warnings.catch_warnings():
            #     warnings.simplefilter("ignore",category=DeprecationWarning)
            #     shop_cate1_encoder = hot_encoder.transform([dicts[shop_cate1]]).toarray()
            # train_x = np.insert(train_x,train_x.shape[1],shop_perpay,axis=1)
            # train_x = np.insert(train_x,train_x.shape[1],shop_score,axis=1)
            # train_x = np.insert(train_x,train_x.shape[1],shop_comment,axis=1)
            # train_x = np.insert(train_x,train_x.shape[1],shop_level,axis=1)
            # for i in range(shop_cate1_encoder.shape[1]):
            #     train_x = np.insert(train_x,train_x.shape[1],shop_cate1_encoder[0][i],axis=1)
            # '''商家信息添加完毕'''

            if all_x is None:
                all_x = train_x
                all_y = train_y
            else:
                all_x = np.insert(all_x,all_x.shape[0],train_x,axis=0)
                all_y = np.insert(all_y,all_y.shape[0],train_y,axis=0)

                # '''添加周几'''
                # extract_weekday = getOneWeekdayFomExtractedData(extractWeekday(part_data, skipNum))
                # train_x = np.append(train_x, extract_weekday, axis=1)
                # ''''''

                # train_x = train_x.reshape((train_x.shape[0],
                #                            train_x.shape[1], 1))
                # print model.get_weights()
                # part_counts = []
                # for i in range(7):
                #     weekday = i + 1
                #     part_count = getOneWeekdayFomExtractedData(count, weekday)
                #     part_counts.append(part_count)


        train_x = all_x
        train_y = all_y

        if needSaveFeature:
            featureAndLabel = np.concatenate((train_x,train_y),axis=1)
            flDF = pd.DataFrame(featureAndLabel, columns=["sameday1","sameday2","sameday3","week_mean1","week_mean2","week_mean3","week_median1","week_median2","week_median3","perpay","score","comment","level","cate1_1","cate1_2","cate1_3","cate1_4","cate1_5","cate1_6","label"])
            if featureSavePath is None:
                if trainAsTest:
                    featureSavePath = "train_feature/%df_%d_%s.csv" % (flDF.shape[1] - 1,cate_level,cate_name)
                else:
                    featureSavePath = "feature/%df_%d_%s.csv" % (flDF.shape[1]-1,cate_level,cate_name)
            flDF.to_csv(featureSavePath)
    else:#有featurePath文件
        flDF = pd.read_csv(featurePath, index_col=0)
        train_x = flDF.values[:, :-1]
        train_y = flDF.values[:, -1:]
        # print train_x
        # print train_y

    '''将t标准化'''
    x_scaler = MinMaxScaler().fit(train_x)
    y_scaler = MinMaxScaler().fit(train_y)
    train_x = x_scaler.transform(train_x)
    train_y = y_scaler.transform(train_y)
    '''标准化结束'''



    '''构造神经网络'''
    h1_activation = "relu"
    rnn_epoch = 60
    verbose = 0
    h_unit = 16
    batch_size = 5
    np.random.seed(128)
    model = Sequential()
    model.add(Dense(h_unit, init="normal", input_dim=train_x.shape[1], activation=h1_activation)) #sigmoid
    model.add(Dense(1, init="normal", activation='linear', activity_regularizer=activity_l2(0.01)))
    sgd = SGD(0.005)
    # rmsprop = RMSprop(0.01)
    # adagrad = Adagrad(0.05)
    adadelta = Adadelta(0.01)
    adam = Adam(0.0001)
    adamax = Adamax(0.01)
    nadam = Nadam(0.01)
    model.compile(loss="mse", optimizer=adam)
    '''构造结束'''

    model.fit(train_x, train_y, nb_epoch=rnn_epoch, batch_size=batch_size, verbose=verbose)

    format = "%Y-%m-%d"
    if trainAsTest:
        startTime = datetime.datetime.strptime("2016-10-18", format)
    else:
        startTime = datetime.datetime.strptime("2016-11-1", format)
    timedelta = datetime.timedelta(1)


    '''预测所有商家'''
    preficts_all = None
    real_all = None
    for j in shopids:
        if j in Parameter.ignore_shopids:
            print "ignore predict", j
            continue
        print "predict:", j
        preficts = []
        part_data = all_data[all_data.shopid == j]
        last_14_real_y = None

        if trainAsTest: #使用训练集后14天作为测试集的话，训练集为前面部分
            last_14_real_y = part_data[len(part_data) - 14:]["count"].values
            part_data = part_data[0:len(part_data) - 14]

        '''预测14天'''
        for i in range(14):
            currentTime = startTime + timedelta * i
            strftime = currentTime.strftime(format)
            # index = getWeekday(strftime) - 1
            # part_count = part_counts[index]
            #取前{sameday_backNum}周同一天的值为特征进行预测
            part_data = part_data.append({"count":0,"shopid":j,"time":strftime,"weekday":getWeekday(strftime)},ignore_index=True)
            x = None
            if sameday_backNum != 0:
                x = getOneWeekdayFomExtractedData(extractBackSameday(part_data,sameday_backNum,part_data.shape[0] - 1, nan_method_sameday_mean))
            if day_back_num != 0 :
                if x is None:
                    x = getOneWeekdayFomExtractedData(extractBackDay(part_data,day_back_num,part_data.shape[0] -1 ,nan_method_sameday_mean))
                else:
                    x = np.concatenate((x,getOneWeekdayFomExtractedData(extractBackDay(part_data,day_back_num,part_data.shape[0] -1 ,nan_method_sameday_mean))),axis=1)
            if weekOrWeekend:
                x = np.concatenate((x, hot_encoder.transform(getOneWeekdayFomExtractedData(extractWorkOrWeekend(part_data,part_data.shape[0] - 1))).toarray()),axis=1)
            for feature in other_features:
                x_value = getOneWeekdayFomExtractedData(extractBackWeekValue(part_data, week_backnum, part_data.shape[0]-1, nan_method_sameday_mean, feature))
                x = np.append(x, x_value, axis=1)
            # '''添加周几'''
            # x = np.append(x, getOneWeekdayFomExtractedData(extractWeekday(part_data, part_data.shape[0]-1)), axis=1)
            # ''''''

            # '''添加商家信息'''
            # index = j - 1
            # oneshopinfo = shop_info.ix[index]
            # shop_perpay = oneshopinfo['perpay'] if not pd.isnull(oneshopinfo['perpay']) else 0
            # shop_score = oneshopinfo['score'] if not pd.isnull(oneshopinfo['score']) else 0
            # shop_comment = oneshopinfo['comment'] if not pd.isnull(oneshopinfo['comment']) else 0
            # shop_level = oneshopinfo['level'] if not pd.isnull(oneshopinfo['level']) else 0
            # shop_cate1 = oneshopinfo['cate1']
            # import warnings
            # with warnings.catch_warnings():
            #     warnings.simplefilter("ignore",category=DeprecationWarning)
            #     shop_cate1_encoder = hot_encoder.transform([dicts[shop_cate1]]).toarray()
            # x = np.insert(x,x.shape[1],shop_perpay,axis=1)
            # x = np.insert(x,x.shape[1],shop_score,axis=1)
            # x = np.insert(x,x.shape[1],shop_comment,axis=1)
            # x = np.insert(x,x.shape[1],shop_level,axis=1)
            # for i in range(shop_cate1_encoder.shape[1]):
            #     x = np.insert(x,x.shape[1],shop_cate1_encoder[0][i],axis=1)
            # '''商家信息添加完毕'''

            x = x_scaler.transform(x)
            # for j in range(sameday_backNum):
            #     x.append(train_y[len(train_y) - (j+1)*7][0])
            # x = np.array(x).reshape((1, sameday_backNum))

            # print x
            # x = x.reshape(1, sameday_backNum, 1)
            predict = model.predict(x)
            if predict.ndim == 2:
                predict = y_scaler.inverse_transform(predict)[0][0]
            elif predict.ndim == 1:
                predict = y_scaler.inverse_transform(predict)[0]

            if(predict <= 0):
                predict == 1
            preficts.append(predict)
            part_data.set_value(part_data.shape[0]-1, "count", predict)

        preficts = (removeNegetive(toInt(np.array(preficts)))).astype(int)
        if preficts_all is None:
            preficts_all = preficts
        else:
            preficts_all = np.insert(preficts_all,preficts_all.shape[0],preficts,axis=0)

        if trainAsTest:
            last_14_real_y = (removeNegetive(toInt(np.array(last_14_real_y)))).astype(int)
            if real_all is None:
                real_all = last_14_real_y
            else:
                real_all = np.insert(real_all,real_all.shape[0],last_14_real_y,axis=0)
                # print preficts,last_14_real_y
            print str(j)+',score:', scoreoneshop(preficts, last_14_real_y)

    # preficts = np.array(preficts)
    preficts_all = preficts_all.reshape((len(shopids)-ignores,14))
    if trainAsTest:
        real_all = real_all.reshape((len(shopids) - ignores,14))
        preficts_all = np.concatenate((preficts_all,real_all), axis=1)
    shopids = shopids.tolist()
    for remove in Parameter.ignore_shopids:
        try:
            shopids.remove(remove)
        except:
            pass
    preficts_all = np.insert(preficts_all, 0, shopids, axis=1)
    if saveFilePath is not None:
        path = saveFilePath + "_%ds_%dd_%df_%d_%s_%d_%d_%d_%s_%dtime.csv" \
                              % (sameday_backNum, day_back_num, train_x.shape[1],cate_level,cate_name
                                 ,rnn_epoch,batch_size,h_unit,h1_activation,time)
        print "save in :", path
        np.savetxt(path,preficts_all,fmt="%d",delimiter=",")
    return preficts_all

def predictAllShop_ANN_part_together_Ntimes(all_data, trainAsTest=False, saveFilePath = None, featurePath = None, cate_level = 0, cate_name = None, featureSavePath = None, needSaveFeature = False, times = 1):
    for i in range(times):
        predictAllShop_ANN_part_together(all_data,trainAsTest,saveFilePath,featurePath,cate_level,cate_name,featureSavePath,needSaveFeature,i+1)

if __name__ == "__main__":
    payinfo = pd.read_csv(Parameter.payAfterGroupingAndRevision2AndTurncate_path)
    # fe_path = Parameter.projectPath + "lzj/train_feature/ann1_168.csv"
    fe_path = None
    time = 3
    predictAllShop_ANN_part_together_Ntimes(payinfo, True, Parameter.projectPath + "result/ANN1_rt_train", fe_path, cate_level=2, cate_name="超市",times=time)