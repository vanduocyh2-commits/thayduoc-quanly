import test from 'node:test';
import assert from 'node:assert/strict';
import {remainingSeconds,clockText} from './client/examClock.mjs';
test('countdown uses absolute deadline, rounds up seconds and stops at zero',()=>{
 assert.equal(remainingSeconds(90001,1),90);assert.equal(remainingSeconds(90001,2),90);assert.equal(remainingSeconds(1001,1),1);assert.equal(remainingSeconds(1001,1002),0);assert.equal(remainingSeconds(null,1002),null);assert.equal(clockText(5400),'01:30:00');assert.equal(clockText(300),'00:05:00');assert.equal(clockText(-1),'00:00:00');
});
