import json, subprocess, re, os
from PIL import Image, ImageDraw, ImageFont
W,H=1920,1080; FPS=30
B='/workspace/bigdata-week11'; os.makedirs(f'{B}/seg',exist_ok=True); os.makedirs(f'{B}/out',exist_ok=True)
def dur(p): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p]))
def sh(*a): subprocess.run(a,check=True)
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'; FONTR='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
def f(sz,bold=True): return ImageFont.truetype(FONT if bold else FONTR, sz, index=3)  # index 3 = TC
def card(path,title,sub,items,shot=None):
    im=Image.new('RGB',(W,H),(30,31,36)); d=ImageDraw.Draw(im)
    if shot:
        sc=Image.open(shot).convert('RGB'); sc=sc.resize((860,int(860*sc.height/sc.width)))
        im.paste(sc,(W-860-60,330)); d.rectangle([W-860-62,328,W-58,330+sc.height+2],outline=(232,160,40),width=3)
    d.rectangle([0,0,W,14],fill=(232,160,40))
    d.text((120,150),title,font=f(72),fill=(255,255,255))
    d.text((120,260),sub,font=f(40,False),fill=(232,160,40))
    y=380
    for it in items:
        d.text((140,y),'•  '+it,font=f(36,False),fill=(220,220,220)); y+=68
    im.save(path)
card(f'{B}/seg/c0.png','student-rental-check','台灣學生租屋行情與避雷｜三角色以上 AI Skill 解說',
     ['資料：內政部實價登錄租賃開放資料（主）＋ 591 刊登（對照）','五個 Agent：collector → fact-checker → quant-analyst →（有風險）devil-advocate → reviewer',
      '測試 A／B／C 皆為 Claude Code 實際執行畫面','成果：final_report.md（行情、真實每月總成本、踩雷提醒）'])
card(f'{B}/seg/c9.png','限制與 AI Tutor','ClassTutor（educatres.github.io/ClassTutor）',
     ['限制：實價登錄只含已申報案件','限制：學校對照表只收少數學校','限制：電費上限無官方原文 → R5 暫不判定',
      '老師頁：匯入字幕 .srt ＋ 講義 →','　貼 YouTube 網址 → 產生課程包','學生頁：載入課程包 → 提問','例：「哪一段證明 Skill 有啟動？」','→ 回答附影片時間點，可點擊跳轉'],
     shot=f'{B}/seg/ct_teacher.png')
nar=json.load(open(f'{B}/narration.json'))
GAP=0.35; LEAD=0.5; TAIL=0.7
cues=[]; t0=0.0; seglist=[]
def split_cues(line):
    parts=re.split(r'(?<=[，。；：！？])',line); parts=[p for p in parts if p.strip()]
    out=[]; cur=''
    for p in parts:
        if len(cur)+len(p)<=30 or not cur: cur+=p
        else: out.append(cur); cur=p
    if cur: out.append(cur)
    return out
for sc in nar:
    s=sc['scene']; n=len(sc['lines'])
    # scene audio
    ds=[dur(f'{B}/tts/{s}_{i}.wav') for i in range(n)]
    Anat=LEAD+sum(ds)+GAP*(n-1)+TAIL
    fct=1.0
    if not s.startswith('c'):
        V0=dur(f'{B}/rec/raw/{s}.mp4')-0.6
        if V0>Anat: fct=min(V0/Anat,1.5)
    at=sc.get('at',[None]*n); cur=LEAD; starts=[]
    for i in range(n):
        st=cur
        if at[i] is not None: st=max(cur,(at[i]-0.6)/fct)
        starts.append(st); cur=st+ds[i]+GAP
    A=cur-GAP+TAIL
    if not s.startswith('c'): A=max(A,V0/fct)
    for i,l in enumerate(sc['lines']):
        cs=split_cues(l); tot=sum(len(c) for c in cs); st=t0+starts[i]
        for c in cs:
            dd=ds[i]*len(c)/tot; cues.append((st,st+dd,c)); st+=dd
    args=['ffmpeg','-loglevel','error','-y','-f','lavfi','-t',f'{A:.3f}','-i','anullsrc=r=48000:cl=stereo']
    fl=[]
    for i in range(n):
        args+=['-i',f'{B}/tts/{s}_{i}.wav']; ms=int(starts[i]*1000); fl.append(f'[{i+1}:a]adelay={ms}|{ms}[a{i}]')
    fl.append(''.join(['[0:a]']+[f'[a{i}]' for i in range(n)])+f'amix=inputs={n+1}:normalize=0:duration=first[o]')
    sh(*args,'-filter_complex',';'.join(fl),'-map','[o]','-c:a','pcm_s16le',f'{B}/seg/{s}.wav')
    A=dur(f'{B}/seg/{s}.wav')
    vout=f'{B}/seg/{s}.mp4'
    if s.startswith('c'):
        sh('ffmpeg','-loglevel','error','-y','-loop','1','-framerate',str(FPS),'-i',f'{B}/seg/{s}.png','-i',f'{B}/seg/{s}.wav','-t',str(A),
           '-c:v','libx264','-pix_fmt','yuv420p','-r',str(FPS),'-c:a','aac','-b:a','160k','-shortest',vout)
    else:
        raw=f'{B}/rec/raw/{s}.mp4'; V=dur(raw)-0.6
        if fct<=1: fct=V/A
        if fct>1:
            vf=f"trim=start=0.6,setpts=(PTS-STARTPTS)/{fct:.4f}"
            if fct>1.15: vf+=f",drawtext=fontfile={FONT}:text='▶ 已加速 ×{fct:.1f}':x=W-tw-40:y=930:fontsize=34:fontcolor=0xE8A028"
        else:
            sl=max(fct,0.65); VL=V/sl
            vf=f"trim=start=0.6,setpts=(PTS-STARTPTS)/{sl:.4f},tpad=stop_mode=clone:stop_duration={max(A-VL,0)+0.2:.2f}"
        sh('ffmpeg','-loglevel','error','-y','-i',raw,'-i',f'{B}/seg/{s}.wav','-filter_complex',f'[0:v]{vf},fps={FPS}[v]','-map','[v]','-map','1:a','-t',str(A),
           '-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',vout)
        print(s,'video',round(V,1),'audio',round(A,1),'factor',round(fct,2))
    seglist.append((s,t0,t0+A)); t0+=A
with open(f'{B}/seg/list.txt','w') as fo:
    for s,_,_ in seglist: fo.write(f"file '{B}/seg/{s}.mp4'\n")
sh('ffmpeg','-loglevel','error','-y','-f','concat','-safe','0','-i',f'{B}/seg/list.txt','-c','copy',f'{B}/seg/nosub.mp4')
def ts(x):
    h=int(x//3600); m=int(x%3600//60); s=x%60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s-int(s))*1000))%1000:03d}"
with open(f'{B}/out/student-rental-check.zh-TW.srt','w') as fo:
    for i,(a,b,c) in enumerate(cues,1): fo.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c}\n\n")
json.dump([{'scene':s,'start':round(a,2),'end':round(b,2)} for s,a,b in seglist],open(f'{B}/seg/scenes.json','w'),ensure_ascii=False,indent=1)
style="FontName=Noto Sans CJK TC,FontSize=26,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&HA0000000,BorderStyle=4,Outline=1,Shadow=0,MarginV=28,Alignment=2"
sh('ffmpeg','-loglevel','error','-y','-i',f'{B}/seg/nosub.mp4','-vf',f"subtitles={B}/out/student-rental-check.zh-TW.srt:force_style='{style}'",
   '-c:v','libx264','-preset','medium','-crf','21','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',f'{B}/out/student-rental-check_final.mp4')
print('total',t0); print(json.dumps(seglist))
