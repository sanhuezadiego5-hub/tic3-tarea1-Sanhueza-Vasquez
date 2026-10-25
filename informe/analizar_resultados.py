import sys,struct,socket,json,collections,statistics,math
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'raspi'))
from imu_protocol import decode_packet,Reassembler


def packets(path):
    data=path.read_bytes(); endian='<' if data[:4]==b'\xd4\xc3\xb2\xa1' else '>'
    link=struct.unpack_from(endian+'I',data,20)[0]
    assert link==1,link
    pos=24
    while pos<len(data):
        sec,usec,inc,orig=struct.unpack_from(endian+'IIII',data,pos);pos+=16
        raw=data[pos:pos+inc];pos+=inc
        if len(raw)<34 or raw[12:14]!=b'\x08\x00':continue
        ip=14;ihl=(raw[ip]&15)*4;total=struct.unpack_from('!H',raw,ip+2)[0]
        proto=raw[ip+9];src=socket.inet_ntoa(raw[ip+12:ip+16]);dst=socket.inet_ntoa(raw[ip+16:ip+20]);p=ip+ihl
        if proto not in (6,17):continue
        sport,dport=struct.unpack_from('!HH',raw,p)
        if proto==6:
            seq=struct.unpack_from('!I',raw,p+4)[0];off=(raw[p+12]>>4)*4;flags=raw[p+13]
        else:seq=0;off=8;flags=0
        yield dict(t=sec+usec/1e6,orig=orig,proto=proto,src=src,dst=dst,sport=sport,dport=dport,seq=seq,flags=flags,payload=raw[p+off:ip+total])

def tcp_messages(ps):
    flows=collections.defaultdict(list)
    for p in ps:
        if p['payload']:
            flows[(p['src'],p['dst'],p['sport'],p['dport'])].append(p)
    for key,group in flows.items():
        group.sort(key=lambda p:p['seq']);raw=bytearray();end=None;spans=[]
        for p in group:
            if end is None:end=p['seq']
            if p['seq']>end:
                print('GAP',key,p['seq']-end,file=sys.stderr);break
            skip=end-p['seq'];piece=p['payload'][skip:]
            if piece:
                raw.extend(piece);end+=len(piece);spans.append((len(raw),p['t']))
        pos=0
        while pos+4<=len(raw):
            n=struct.unpack_from('!I',raw,pos)[0]
            if not 96<=n<=1200 or pos+4+n>len(raw):break
            endpos=pos+4+n
            timestamp=next(t for stop,t in spans if stop>=endpos)
            yield key,timestamp,bytes(raw[pos+4:endpos])
            pos=endpos

def analysis(path):
    ps=list(packets(path));data=[p for p in ps if 5001 in (p['sport'],p['dport'])]
    tcp=[p for p in data if p['proto']==6];udp=[p for p in data if p['proto']==17]
    msgs=list(tcp_messages(tcp))+[(None,p['t'],p['payload']) for p in udp]
    assembler=Reassembler(timeout=100000,max_pending=256)
    blocks=[];types=collections.Counter();errors=[];times=[];encodings=collections.Counter()
    for flow,t,msg in msgs:
        try:
            h,_=decode_packet(msg);types[h['type']]+=1
            if h['type']==2:
                times.append(t);encodings['json' if msg.startswith(b'{') else 'binary']+=1
                b=assembler.push(msg,now=0)
                if b and not b['duplicate']:blocks.append(b)
        except Exception as e:errors.append(str(e))
    totals={}
    for st in (0,1):
        bs=[b for b in blocks if b['stream']==st]
        totals[st]=dict(blocks=len(bs),samples=sum(b['sample_count'] for b in bs),windows=[b['window_seq'] for b in bs],
                       modes=sorted(set('sequential' if b['flags']&8 else 'parallel' for b in bs)))
    return dict(file=path.name,capture_seconds=ps[-1]['t']-ps[0]['t'],data_packets=len(data),
                packets_by_transport={'tcp':len(tcp),'udp':len(udp)},frame_bytes=sum(p['orig'] for p in data),
                esp_to_pi_packets=sum(p['dport']==5001 for p in data),pi_to_esp_packets=sum(p['sport']==5001 for p in data),
                transport_payload_bytes=sum(len(p['payload']) for p in data),syn=sum(bool(p['flags']&2) for p in tcp),
                data_delivery_span_seconds=max(times)-min(times) if times else 0,
                decoded_message_types=dict(types),encodings=dict(encodings),totals=totals,
                incomplete_blocks=len(assembler.pending),decode_errors=errors[:10])

def main():
    import argparse
    parser=argparse.ArgumentParser(description='Recalcula la evidencia PCAP y las sesiones históricas del informe TIC3.')
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('analisis_resultados.json'))
    args=parser.parse_args()
    network=[]
    for path in sorted((BASE/'wireshark/ap').glob('*.pcap')):
        result=analysis(path)
        transport=17 if result['encodings'] and 'udp' in path.name.lower() else 6
        selected=[p for p in packets(path) if p['proto']==transport and 5001 in (p['sport'],p['dport'])]
        result['selected_transport_packets']=len(selected)
        result['selected_transport_frame_bytes']=sum(p['orig'] for p in selected)
        network.append(result)
    blocks=[json.loads(p.read_text()) for p in (BASE/'sensores').glob('**/window-*.json')]
    sensors=[]
    for path in sorted((BASE/'sensores/sessions').glob('*.json')):
        manifest=json.loads(path.read_text());config=manifest['configuration']
        acc=[b for b in blocks if b.get('session_id')==manifest['id'] and b['stream']==0]
        rows=[b['values'][i:i+3] for b in acc for i in range(0,len(b['values']),3)]
        sensors.append(dict(session=manifest['id'],config=config,acc_samples=len(rows),
            gyro_samples=sum(b['sample_count'] for b in blocks if b.get('session_id')==manifest['id'] and b['stream']==1),
            raw_z_mean=statistics.mean(row[2] for row in rows),
            norm_mean=statistics.mean(math.sqrt(sum((v*config['accel_range']*9.80665/32768)**2 for v in row)) for row in rows),
            lsb=config['accel_range']*9.80665/32768))
    args.output.write_text(json.dumps(dict(sensor_sessions=sensors,network_captures=network,
        method='Ethernet/IPv4 PCAP; tramas filtradas por transporte y puerto 5001. Mensajes TIC3 reensamblados y validados con el codec del proyecto. El intervalo DATA no es latencia absoluta.'),indent=2,ensure_ascii=False))
    print(args.output)

if __name__=='__main__':
    main()
