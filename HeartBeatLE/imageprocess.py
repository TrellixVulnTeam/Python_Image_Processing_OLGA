import cv2import numpy as npimport timefrom numpy import  array, hammingimport matplotlib.pyplot as pltfrom sklearn.manifold import SpectralEmbeddingfrom movefilter import ave_movefrom scipy.signal import butter,lfilterfrom scipy.interpolate import CubicSplineclass findFaceGetPluse():    def __init__(self):        self.t = time.time()        self.fiter=ave_move()        self.face_cascade = cv2.CascadeClassifier("./lib/haarcascade_frontalface_alt.xml")        self.le = SpectralEmbedding(n_components=1, affinity='nearest_neighbors', n_neighbors=12)        self.frame_in = np.zeros((10, 10))        self.frame_out = np.zeros((10, 10))        self.dect = np.zeros((10, 10)) # using debug        self.x, self.y, self.w, self.h = 0, 0, 0, 0        self.dx, self.dx1 = 0, 0        self.t0=time.time()        self.val_b = []        self.val_g = []        self.val_r = []        self.times = []        self.buffersize = 270    def detecor(self):        self.frame_out = self.frame_in        gray = cv2.cvtColor(self.frame_in, cv2.COLOR_BGR2GRAY)        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)        try:            self.x, self.y, self.w, self.h = faces[0]            # self.frame_out = self.frame_in            self.dx = int(self.x+self.w*0.2)            self.dx1 = int(self.x+self.w*0.8)            cv2.rectangle(self.frame_out, (self.dx, self.y), (self.dx1, self.y+self.h), (0, 255, 0), 1)            self.dect = self.frame_in[self.y:self.y+self.h, self.dx:self.dx1]            return self.dx, self.y, self.dx1, self.y+self.h        except:            return None    def get_mean(self, rect, img):        x1, y1, x2, y2 = rect        sub_face = img[y1:y2, x1:x2, :]        val_b = np.mean(sub_face[:, :, 0])        val_g = np.mean(sub_face[:, :, 1])        val_r = np.mean(sub_face[:, :, 2])        return val_b, val_g, val_r    def butter_bandpass(self,lowcut, highcut, fs, order=5):        nyq = 0.5 * fs        low = lowcut / nyq        high = highcut / nyq        b, a = butter(order, [low, high], btype='bandpass')        return b, a    def butter_bandpass_filter(self,data, lowcut, highcut, fs, order=5):        b, a = self.butter_bandpass(lowcut, highcut, fs, order=order)        y = lfilter(b, a, data)        return y    def build_data(self):        rect = self.detecor()        if rect != None:            val = self.get_mean(rect, self.frame_in)            self.val_b.append(val[0])            self.val_g.append(val[1])            self.val_r.append(val[2])            self.times.append(time.time()-self.t0)            L = len(self.times)            # delaytime = self.times[-1] - self.times[0]            # if delaytime > 10 and delaytime < 12:            #     self.buffersize = len(self.times)            # else:            #     self.buffersize+=1            if L > self.buffersize:                self.val_r, self.val_g, self.val_b = self.val_r[-self.buffersize:], self.val_g[                                                                                    -self.buffersize:], self.val_b[                                                                                                        -self.buffersize:]                self.times = self.times[-self.buffersize:]            if L >= 12:                t=array(self.times)                b, g, r = array(self.val_b), array(self.val_g), array(self.val_r)                b, g, r = b.reshape(1, b.shape[0]), g.reshape(1, g.shape[0]), r.reshape(1, r.shape[0])                X = np.concatenate((r, g, b)) # build data                X = X.T                # print(X.shape) # debug                Y=self.le.fit_transform(X) # Laplacian Eigenmaps                Y=Y.T                Y=np.squeeze(Y)                return Y,t        else:            return None    def get_pluse(self):        val=self.build_data()        if  val  is None:            pass        else:            data,t=val            # print(len(data))            if len(data)>269:                """                remove singpoint and 0.7-4 hz fitter not implement                """                #five point move avage fitter                for i in range(len(data)):                    data[i]=self.fiter.move_ave(data[i],5)                self.fiter.clear()                # hamming window    15 point                hamming_win=array(hamming(15).tolist()*int(len(data)/15))                data_h=data*hamming_win                ydata=self.butter_bandpass_filter(data_h,0.7,4,30,8) #bandpass                cs=CubicSpline(t,ydata)                data_c=cs(t)                data_d=np.diff(data_c,1)                data_m=[]                data_t=[]                i=0                while i<len(data_d)-14:                    maxpoint=max(data_d[i:i+15])                    idx=np.where(data_d[i:i+15]==maxpoint)                    # print(idx[0][0])                    idx_t=i+idx[0][0]                    # print(idx_t)                    data_t.append(t[idx_t])                    data_m.append(maxpoint)                    i=i+15                # print(data_t)                time_t=np.diff(data_t,1)                k=0                # print(time_t)                for i in range(len(time_t)):                    if time_t[i]>2 :                        k+=1                    if time_t[i]<0.25:                        k-=1                # print("k:",k)                T=np.sum(time_t)/(len(time_t)+k)                rate=60/T                text="RPPG:{}".format(rate)                cv2.putText(self.frame_out,text,(10, 125),cv2.FONT_HERSHEY_PLAIN, 2, (0,255,0))                return data ,t ,data_h,ydata,data_c,data_m,data_t            else:                return Noneif __name__ == '__main__':    run = findFaceGetPluse()    video = cv2.VideoCapture(0)    cv2.namedWindow("demo")    cv2.namedWindow("dect")    plt.ion()    plt.show()    # _, axes = plt.subplots(nrows=4, ncols=1, figsize=plt.figaspect(0.33))    # axes[0].set_axis_off()    #    # axes[0] = plt.subplot(411)    while cv2.waitKey(10) != 27:        _, img = video.read()        run.frame_in = img        val = run.get_pluse()        val1=run.build_data()        if val !=None:            data,ts,data_h,y_data,h,data_m,data_t=val            # data ,t=val1            # if len(data)>269:                # print(len(data),len(h))                # axes[0].cla()                # axes[0].set_title('move filter data')                #                # axes[0].plot(ts,data)                #                # axes[1].cla()                # axes[1].set_title('hamming window data')                # axes[1].plot(ts,data_h)                # axes[2].cla()                # axes[2].set_title('bandpass filter')                # axes[2].plot(ts,y_data)                # axes[3].cla()                # axes[3].plot(ts,h)                # axes[3].scatter(data_t,data_m)                # plt.pause(0.5)        cv2.imshow("demo", run.frame_out)        cv2.imshow("dect", run.dect)    video.release()