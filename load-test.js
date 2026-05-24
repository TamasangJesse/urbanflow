import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },
    { duration: '1m', target: 400 },
    { duration: '30s', target: 0 },
  ],
};

export default function () {
  let res = http.get('https://urbanflow.duckdns.org');
  check(res, { 'frontend status 200': (r) => r.status === 200 });

 
  sleep(1);
}