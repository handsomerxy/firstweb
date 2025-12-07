import os 
import argparse 
import threading 
import nls 

DEFAULT_URL = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1" 

DEFAULT_TEXT = "从前，在一个遥远的村庄里，住着一位善良的小女孩艾拉。她每天都会到森林里采摘美丽的花朵，和森林里的小动物们成为好朋友。一天，艾拉在森林深处发现了一朵会发光的神奇花朵，当她轻轻触碰花瓣时，花朵突然绽放出七彩的光芒，整个森林都被这美丽的光芒照亮了。从此，每当夜晚降临，这朵神奇的花朵就会发出温暖的光芒，守护着整个村庄，而艾拉也成为了村庄的守护者，用她的善良和勇气保护着所有的村民。" 


class TestTts: 
    def __init__(self, tid, out_file, url, token, appkey, voice, aformat, trace): 
        self.__th = threading.Thread(target=self.__test_run) 
        self.__id = tid 
        self.__out_file = out_file 
        self.__url = url 
        self.__token = token 
        self.__appkey = appkey 
        self.__voice = voice 
        self.__aformat = aformat 
        self.__trace = trace 

    def start(self, text): 
        self.__text = text 
        out_dir = os.path.dirname(self.__out_file) 
        if out_dir: 
            os.makedirs(out_dir, exist_ok=True) 
        self.__f = open(self.__out_file, "wb") 
        self.__th.start() 

    def join(self): 
        self.__th.join() 

    def test_on_metainfo(self, message, *args): 
        print("on_metainfo message={}".format(message)) 

    def test_on_error(self, message, *args): 
        print("on_error args={}".format(args)) 

    def test_on_close(self, *args): 
        print("on_close: args={}".format(args)) 
        try: 
            self.__f.close() 
        except Exception as e: 
            print("close file failed since:", e) 

    def test_on_data(self, data, *args): 
        try: 
            self.__f.write(data) 
        except Exception as e: 
            print("write data failed:", e) 

    def test_on_completed(self, message, *args): 
        print("on_completed: args={} message={}".format(args, message)) 

    def __test_run(self): 
        print("thread:{} start..".format(self.__id)) 
        if self.__trace: 
            nls.enableTrace(True) 
        tts = nls.NlsSpeechSynthesizer( 
            url=self.__url, 
            token=self.__token, 
            appkey=self.__appkey, 
            on_metainfo=self.test_on_metainfo, 
            on_data=self.test_on_data, 
            on_completed=self.test_on_completed, 
            on_error=self.test_on_error, 
            on_close=self.test_on_close, 
            callback_args=[self.__id], 
        ) 
        print("{}: session start".format(self.__id)) 
        r = tts.start(self.__text, voice=self.__voice, aformat=self.__aformat) 
        print("{}: tts done with result:{}".format(self.__id, r)) 


def main(): 
    parser = argparse.ArgumentParser() 
    parser.add_argument("--url", default=DEFAULT_URL) 
    parser.add_argument("--token") 
    parser.add_argument("--appkey") 
    parser.add_argument("--text", default=DEFAULT_TEXT) 
    parser.add_argument("--voice", default="ailun")      
    parser.add_argument("--format", default="wav") 
    parser.add_argument("--out", default=os.path.join("tests", "test_tts.wav")) 
    parser.add_argument("--threads", type=int, default=1) 
    parser.add_argument("--trace", action="store_true") 
    args = parser.parse_args() 

    token = args.token or os.getenv("ALIYUN_NLS_TOKEN", "") 
    appkey = args.appkey or os.getenv("ALIYUN_NLS_APPKEY", "") 
    if not token or not appkey: 
        raise SystemExit("missing token or appkey") 

    tasks = [] 
    if args.threads <= 1: 
        t = TestTts( 
            "thread0", 
            args.out, 
            args.url, 
            token, 
            appkey, 
            args.voice, 
            args.format, 
            args.trace, 
        ) 
        t.start(args.text) 
        tasks.append(t) 
    else: 
        base, ext = os.path.splitext(args.out) 
        for i in range(args.threads): 
            out = f"{base}_{i}{ext or '.wav'}" 
            t = TestTts( 
                f"thread{i}", 
                out, 
                args.url, 
                token, 
                appkey, 
                args.voice, 
                args.format, 
                args.trace, 
            ) 
            t.start(args.text) 
            tasks.append(t) 

    for t in tasks: 
        t.join() 


if __name__ == "__main__": 
    main()