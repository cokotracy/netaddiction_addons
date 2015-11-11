  1 /**
  2  * LineaBrowser class used to communicate between the Linea device and javascript.
  3  * @constructor
  4  * @namespace LineaBrowser Class
  5  */
  6 LineaBrowser = function (){
  7 	var deligates = {
  8 		buttonPress: [],
  9 		buttonRelease: [],
 10 		barcodeData: [],
 11 		magneticCardData: [],
 12 		magneticCardRawData: [],
 13 		magneticCardEncryptedData: [],
 14 		magneticCardEncryptedRawData: [],
 15 		connectionState: [],
 16 		creditCardData: []
 17 	};
 18 	var scopes = {
 19 		buttonPress: [],
 20 		buttonRelease: [],
 21 		barcodeData: [],
 22 		magneticCardData: [],
 23 		magneticCardRawData: [],
 24 		magneticCardEncryptedData: [],
 25 		magneticCardEncryptedRawData: [],
 26 		connectionState: [],
 27 		creditCardData: []
 28 	};
 29 	var commandQueue = '';
 30 	var addToQueue = function (command, args){
 31 		var builtArgs = '';
 32 		var len = args.length;
 33 		for(var i=0;i<len;i++){
 34 			if(args[i] instanceof Array)
 35 				args[i] = args[i].join(',');
 36 			builtArgs += ':' + args[i];
 37 		}
 38 		if(!commandQueue)
 39 			commandQueue = 'lineaBrowser://' + command + builtArgs;
 40 		else
 41 			commandQueue += '&' + command + builtArgs;
 42 		window.location.href = commandQueue;
 43 	};
 44 	/**
 45 	 * @lends LineaBrowser
 46 	 */
 47 	return {
 48 		//CONN_STATES
 49 		/**
 50 		 * For Connection State Changes
 51 		 * @constant
 52 		 */
 53 		CONN_DISCONNECTED:0,
 54 		/**
 55 		 * For Connection State Changes
 56 		 * @constant
 57 		 */
 58 		CONN_CONNECTING:1,
 59 		/**
 60 		 * For Connection State Changes
 61 		 * @constant
 62 		 */
 63 		CONN_CONNECTED:2,
 64 		/**
 65 		 * For Scan Modes
 66 		 * @constant
 67 		 */
 68 		MODE_SINGLE_SCAN:0,
 69 		/**
 70 		 * For Scan Modes
 71 		 * @constant
 72 		 */
 73 		MODE_MULTI_SCAN:1,
 74 
 75 		/**
 76 		 * For Button States
 77 		 * @constant
 78 		 */
 79 		BUTTON_DISABLED:0,
 80 		/**
 81 		 * For Button States
 82 		 * @constant
 83 		 */
 84 		BUTTON_ENABLED:1,
 85 		/**
 86 		 * For Card Processing
 87 		 * @constant
 88 		 */
 89 		MS_PROCESSED_CARD_DATA:0,
 90 		/**
 91 		 * For Card Processing
 92 		 * @constant
 93 		 */
 94 		MS_RAW_CARD_DATA:1,
 95 		/**
 96 		 * For Barcode Scan Type Return Mode
 97 		 * @constant
 98 		 */
 99 		BARCODE_TYPE_DEFAULT:0,
100 		/**
101 		 * For Barcode Scan Type Return Mode
102 		 * @constant
103 		 */
104 		BARCODE_TYPE_EXTENDED:1,
105 
106 		/**
107 		 * For Naming Barcode Types (used in Scan listeners and Setting any barcode type data)
108 		 * @type LineaBrowser.BAR_TYPES
109 		 * @constructor
110 		 */
111 		BAR_TYPES: {
112 			/** @constant */
113 			BAR_ALL: 0,
114 			/** @constant */
115 			BAR_UPC: 1,
116 			/** @constant */
117 			BAR_CODABAR: 2,
118 			/** @constant */
119 			BAR_CODE25_NI2OF5: 3,
120 			/** @constant */
121 			BAR_CODE25_I2OF5: 4,
122 			/** @constant */
123 			BAR_CODE39: 5,
124 			/** @constant */
125 			BAR_CODE93: 6,
126 			/** @constant */
127 			BAR_CODE128: 7,
128 			/** @constant */
129 			BAR_CODE11: 8,
130 			/** @constant */
131 			BAR_CPCBINARY: 9,
132 			/** @constant */
133 			BAR_DUN14: 10,
134 			/** @constant */
135 			BAR_EAN2: 11,
136 			/** @constant */
137 			BAR_EAN5: 12,
138 			/** @constant */
139 			BAR_EAN8: 13,
140 			/** @constant */
141 			BAR_EAN13: 14,
142 			/** @constant */
143 			BAR_EAN128: 15,
144 			/** @constant */
145 			BAR_GS1DATABAR: 16,
146 			/** @constant */
147 			BAR_ITF14: 17,
148 			/** @constant */
149 			BAR_LATENT_IMAGE: 18,
150 			/** @constant */
151 			BAR_PHARMACODE: 19,
152 			/** @constant */
153 			BAR_PLANET: 20,
154 			/** @constant */
155 			BAR_POSTNET: 21,
156 			/** @constant */
157 			BAR_INTELLIGENT_MAIL: 22,
158 			/** @constant */
159 			BAR_MSI: 23,
160 			/** @constant */
161 			BAR_POSTBAR: 24,
162 			/** @constant */
163 			BAR_RM4SCC: 25,
164 			/** @constant */
165 			BAR_TELEPEN: 26,
166 			/** @constant */
167 			BAR_PLESSEY: 27,
168 			/** @constant */
169 			BAR_PDF417: 28,
170 			/** @constant */
171 			BAR_MICROPDF417: 29,
172 			/** @constant */
173 			BAR_DATAMATRIX: 30,
174 			/** @constant */
175 			BAR_AZTEK: 31,
176 			/** @constant */
177 			BAR_QRCODE: 32,
178 			/** @constant */
179 			BAR_MAXICODE: 33,
180 			/** @constant */
181 			BAR_LAST: 34,
182 
183 			/** @constant */
184 			BAR_EX_ALL:0,
185 			/** @constant */
186 			BAR_EX_UPCA:1,
187 			/** @constant */
188 			BAR_EX_CODABAR:2,
189 			/** @constant */
190 			BAR_EX_CODE25_NI2OF5:3,
191 			/** @constant */
192 			BAR_EX_CODE25_I2OF5:4,
193 			/** @constant */
194 			BAR_EX_CODE39:5,
195 			/** @constant */
196 			BAR_EX_CODE93:6,
197 			/** @constant */
198 			BAR_EX_CODE128:7,
199 			/** @constant */
200 			BAR_EX_CODE11:8,
201 			/** @constant */
202 			BAR_EX_CPCBINARY:9,
203 			/** @constant */
204 			BAR_EX_DUN14:10,
205 			/** @constant */
206 			BAR_EX_EAN2:11,
207 			/** @constant */
208 			BAR_EX_EAN5:12,
209 			/** @constant */
210 			BAR_EX_EAN8:13,
211 			/** @constant */
212 			BAR_EX_EAN13:14,
213 			/** @constant */
214 			BAR_EX_EAN128:15,
215 			/** @constant */
216 			BAR_EX_GS1DATABAR:16,
217 			/** @constant */
218 			BAR_EX_ITF14:17,
219 			/** @constant */
220 			BAR_EX_LATENT_IMAGE:18,
221 			/** @constant */
222 			BAR_EX_PHARMACODE:19,
223 			/** @constant */
224 			BAR_EX_PLANET:20,
225 			/** @constant */
226 			BAR_EX_POSTNET:21,
227 			/** @constant */
228 			BAR_EX_INTELLIGENT_MAIL:22,
229 			/** @constant */
230 			BAR_EX_MSI_PLESSEY:23,
231 			/** @constant */
232 			BAR_EX_POSTBAR:24,
233 			/** @constant */
234 			BAR_EX_RM4SCC:25,
235 			/** @constant */
236 			BAR_EX_TELEPEN:26,
237 			/** @constant */
238 			BAR_EX_UK_PLESSEY:27,
239 			/** @constant */
240 			BAR_EX_PDF417:28,
241 			/** @constant */
242 			BAR_EX_MICROPDF417:29,
243 			/** @constant */
244 			BAR_EX_DATAMATRIX:30,
245 			/** @constant */
246 			BAR_EX_AZTEK:31,
247 			/** @constant */
248 			BAR_EX_QRCODE:32,
249 			/** @constant */
250 			BAR_EX_MAXICODE:33,
251 			/** @constant */
252 			BAR_EX_RESERVED1:34,
253 			/** @constant */
254 			BAR_EX_RESERVED2:35,
255 			/** @constant */
256 			BAR_EX_RESERVED3:36,
257 			/** @constant */
258 			BAR_EX_RESERVED4:37,
259 			/** @constant */
260 			BAR_EX_RESERVED5:38,
261 			/** @constant */
262 			BAR_EX_UPCA_2:39,
263 			/** @constant */
264 			BAR_EX_UPCA_5:40,
265 			/** @constant */
266 			BAR_EX_UPCE:41,
267 			/** @constant */
268 			BAR_EX_UPCE_2:42,
269 			/** @constant */
270 			BAR_EX_UPCE_5:43,
271 			/** @constant */
272 			BAR_EX_EAN13_2:44,
273 			/** @constant */
274 			BAR_EX_EAN13_5:45,
275 			/** @constant */
276 			BAR_EX_EAN8_2:46,
277 			/** @constant */
278 			BAR_EX_EAN8_5:47,
279 			/** @constant */
280 			BAR_EX_CODE39_FULL:48,
281 			/** @constant */
282 			BAR_EX_ITA_PHARMA:49,
283 			/** @constant */
284 			BAR_EX_CODABAR_ABC:50,
285 			/** @constant */
286 			BAR_EX_CODABAR_CX:51,
287 			/** @constant */
288 			BAR_EX_SCODE:52,
289 			/** @constant */
290 			BAR_EX_MATRIX_2OF5:53,
291 			/** @constant */
292 			BAR_EX_IATA:54,
293 			/** @constant */
294 			BAR_EX_KOREAN_POSTAL:55,
295 			/** @constant */
296 			BAR_EX_CCA:56,
297 			/** @constant */
298 			BAR_EX_CCB:57,
299 			/** @constant */
300 			BAR_EX_CCC:58,
301 			/** @constant */
302 			BAR_EX_LAST:59
303 		},
304 		/**
305 		 * Clears the queue of commands about to be sent to the LineaBrowser app.
306 		 * @public
307 		 */
308 		clearCommandQueue: function(){
309 			commandQueue = '';
310 			window.location.href = 'javascript:void(0);';
311 		},
312 		/**
313 		 * Adds an event listener to the specified event.
314 		 * @param {String} event The event name to attach function to.
315 		 * @param {Function} fn The function to execute when event fires.
316 		 * @public
317 		 */
318 		on: function (event, fn, scope){
319 			if(typeof deligates[event] == 'undefined'){
320 				throw "LineaBrowser.on: first argument must be a valid event.";
321 				return false;
322 			}
323 			if(!(fn instanceof Function)){
324 				throw "LineaBrowser.on: second argument must be of type function.";
325 				return false;
326 			}
327 			deligates[event].push(fn);
328 			scopes[event].push(scope || window);
329 			return true;
330 		},
331 		/**
332 		 * Removes an event listener.
333 		 * @param {String} event The event name to search for function in.
334 		 * @param {Function} fn The function to remove.
335 		 * @public
336 		 */
337 		un: function (event, fn){
338 			if(typeof deligates[event] == 'undefined'){
339 				throw "LineaBrowser.un: first argument must be a valid event.";
340 				return false;
341 			}
342 			var len = deligates[event].length;
343 			for(var i=0;i<len;i++)
344 				if(deligates[event][i] === fn){
345 					deligates[event].splice(i, 1);
346 					scopes[event].splice(i, 1);
347 					return true;
348 				}
349 			return false;
350 		},
351 		/**
352 		 * Enables or disables the specified barcode.
353 		 * @param {Integer} barcodeType The specified barcode of LineaBrowser.BAR_TYPES.*
354 		 * @param {Boolean} enabled Weather the barcode will be enabled or disabled.
355 		 * @public
356 		 */
357 		enableBarcode: function (barcodeType, enabled){
358 			barcodeType = parseInt(barcodeType) || 0;
359 			enabled = (enabled)?1:0;
360 			addToQueue('enableBarcode', [barcodeType, enabled]);
361 			return true;
362 		},
363 		/**
364 		 * Plays a sound though the Linea device.
365 		 * @param {Integer} volume The volume to play sound at (Currently the Linea device does not support other values than 0 or 100).
366 		 * @param {Array} beepData An array of data to play.
367 		 * @example LineaBrowser.playSound(100, [1000, 200, 4000, 100, 100, 500]); // This will play as the following: 1000mhz @ 200ms, 4000mhz @ 100ms, 100mhz @ 500ms
368 		 * @public
369 		 */
370 		playSound: function (volume, beepData){
371 			volume = parseInt(volume) || 0;
372 			if(!(beepData instanceof Array)){
373 				throw "Error on LineaBrowser.playSound: second argument must be an array";
374 				return false;
375 			}
376 			var len = beepData.length;
377 			for(var i=0;i<len;i++)
378 				beepData[i] = parseInt(beepData[i]) || 0;
379 			addToQueue('playSound', [volume, beepData]);
380 			return true;
381 		},
382 		/**
383 		 * Turns on the barcode lazer (it will accept barcodes).
384 		 * @public
385 		 */
386 		startScan: function (){
387 			addToQueue('startScan', []);
388 			return true;
389 		},
390 		/**
391 		 * Turns off the barcode lazer (it will stop accepting barcodes).
392 		 * @public
393 		 */
394 		stopScan: function (){
395 			addToQueue('stopScan', []);
396 			return true;
397 		},
398 		/**
399 		 * Used to turn off the lazer after a the specified amount of time has passed without scanning a barcode.
400 		 * @param {Integer} timeout The time in seconds to turn off lazer on no barcode scan (0 will never timeout).
401 		 * @public
402 		 */
403 		setScanTimeout: function (timeout){
404 			timeout = parseInt(timeout) || 0;
405 			addToQueue('setScanTimeout', [timeout]);
406 			return true;
407 		},
408 		/**
409 		 * Used to specifiy weather the button on the device will activate the lazer when pressed. (the buttonPress and buttonRelease event will still fire)
410 		 * @param {Integer} mode One of the following: LineaBrowser.BUTTON_DISABLED or LineaBrowser.BUTTON_ENABLED
411 		 * @public
412 		 */
413 		setScanButtonMode: function (mode){
414 			mode = (mode)?1:0;
415 			addToQueue('setScanButtonMode', [mode]);
416 			return true;
417 		},
418 		/**
419 		 * Used to tell the barcode engine to go into persistant scanning or not. Persistant scanning will keep
420 		 * the lazer active even when a barcode is scanned allowing you to scan multiple barcodes in sequence
421 		 * without having to keep pressing and depressing the button.
422 		 * @param {Integer} mode The mode the barcode engine goes into. Should be on of the following: LineaBrowser.MODE_SINGLE_SCAN or LineaBrowser.MODE_MULTI_SCAN.
423 		 * @public
424 		 */
425 		setScanMode: function (mode){
426 			mode = (mode)?1:0;
427 			addToQueue('setScanMode', [mode]);
428 			return true;
429 		},
430 		/**
431 		 * Sets the beep settings for when a barcode is successfully scanned.
432 		 * @param {Boolean} Weather the beep should play or not.
433 		 * @param {Integer} Volume to play the sound at (Currently the Linea device does not support this).
434 		 * @param {Array} Beep data to send (see LineaBrowser.playSound for more info)
435 		 * @public
436 		 */
437 		setScanBeep: function (enabled, volume, beepData){
438 			enabled = (enabled)?1:0;
439 			volume = parseInt(volume) || 0;
440 			if(!(beepData instanceof Array)){
441 				throw "Error on LineaBrowser.playSound: second argument must be an array";
442 				return false;
443 			}
444 			if(!(beepData instanceof Array)){
445 				throw "Error on LineaBrowser.setScanBeep: forth argument must be an array";
446 				return false;
447 			}
448 			var len = beepData.length;
449 			for(var i=0;i<len;i++)
450 				beepData[i] = parseInt(beepData[i]) || 0;
451 			addToQueue('setScanBeep', [enabled, volume, beepData]);
452 			return true;
453 		},
454 		/**
455 		 * Hides the config bar at the bottom of the screen to give more realestate or to make your own. (this will resize the window size)
456 		 * @public
457 		 */
458 		hideConfigBar:function (){
459 			addToQueue('hideConfigBar', []);
460 			return true;
461 		},
462 		/**
463 		 * Shows the config bar at the bottom of the screen. (this will resize the window size)
464 		 * @public
465 		 */
466 		showConfigBar: function (){
467 			addToQueue('showConfigBar', []);
468 			return true;
469 		},
470 		/**
471 		 * Sets the mode which the card reader data is returned. If MS_PROCESSED_CARD_DATA is used it will return with magneticCardData event
472 		 * if MS_RAW_CARD_DATA is used it will return the card data with magenticCardRawData.
473 		 * @param {Integer} mode The mode to use. (should be one of the following LineaBrowser.MS_PROCESSED_CARD_DATA or LineaBrowser.MS_RAW_CARD_DATA)
474 		 * @public
475 		 */
476 		setMSCardDataMode: function (mode){
477 			mode = parseInt(mode) || 0;
478 			addToQueue('setMSCardDataMode', [mode]);
479 			return true;
480 		},
481 		/**
482 		 * Sets which barcode type subset is used for returning. If BARCODE_TYPE_DEFAULT is used it will use
483 		 * LineaBrowser.BAR_TYPES.*(^_EX) (without the _EX extension). If BARCODE_TYPE_EXTENDED is used it wil
484 		 * return barcode types using LineaBrowser.BAR_TYPES.*_EX (with the _EX extension).
485 		 * @param {Integer} mode The mode to return the barcode type as. (Should be one of LineaBrowser.BARCODE_TYPE_DEFAULT or LineaBrowser.BARCODE_TYPE_EXTENDED)
486 		 * @public
487 		 */
488 		setBarcodeTypeMode: function (mode){
489 			mode = parseInt(mode) || 0;
490 			addToQueue('setBarcodeTypeMode', [mode]);
491 			return true;
492 		},
493 		/**
494 		 * This function will be fired when the button is pressed on the LineaDevice. You may attach a listener to this by calling:
495 		 * <pre><code>
496 		 *  LineaBrowser.on('buttonPressed', function (button){
497 		 *      // Your Code
498 		 *  });
499 		 * </code></pre>
500 		 * The first parameter is which button was pressed, however it will always return 0 currently.
501 		 * @private
502 		 */
503 		buttonPressed: function (){
504 			var len = deligates.buttonPress.length;
505 			for(var i=0;i<len;i++)
506 				deligates.buttonPress[i].apply(scopes.buttonPress[i], arguments);
507 		},
508 		/**
509 		 * This function will be fired when the button is released on the LineaDevice. You may attach a listener to this by calling:
510 		 * <pre><code>
511 		 *  LineaBrowser.on('buttonReleased', function (button){
512 		 *      // Your Code
513 		 *  });
514 		 * </code></pre>
515 		 * The first parameter is which button was pressed, however it will always return 0 currently.
516 		 * @private
517 		 */
518 		buttonReleased: function (){
519 			var len = deligates.buttonRelease.length;
520 			for(var i=0;i<len;i++)
521 				deligates.buttonRelease[i].apply(scopes.buttonRelease[i], arguments);
522 		},
523 		/**
524 		 * This function will be fired when a card is successfully read on the LineaDevice. You may attach a listener to this by calling:
525 		 * <pre><code>
526 		 *  LineaBrowser.on('magneticCardData', function (track1, track2, track3){
527 		 *      // Your Code
528 		 *  });
529 		 * </code></pre>
530 		 * The parameters passed are track1, track2, and track3.
531 		 * @private
532 		 */
533 		magneticCardData: function (){
534 			var len = deligates.magneticCardData.length;
535 			for(var i=0;i<len;i++)
536 				deligates.magneticCardData[i].apply(scopes.magneticCardData[i], arguments);
537 		},
538 		/**
539 		 * Currently not fully supported!
540 		 */
541 		magneticCardRawData: function (){
542 			var len = deligates.magneticCardRawData.length;
543 			for(var i=0;i<len;i++)
544 				deligates.magneticCardRawData[i].apply(scopes.magneticCardRawData[i], arguments);
545 		},
546 		/**
547 		 * Currently not fully supported!
548 		 */
549 		magneticCardEncryptedData: function (){
550 			var len = deligates.magneticCardEncryptedData.length;
551 			for(var i=0;i<len;i++)
552 				deligates.magneticCardEncryptedData[i].apply(scopes.magneticCardEncryptedData[i], arguments);
553 		},
554 		/**
555 		 * Currently not fully supported!
556 		 */
557 		magneticCardEncryptedRawData: function (){
558 			var len = deligates.magneticCardEncryptedRawData.length;
559 			for(var i=0;i<len;i++)
560 				deligates.magneticCardEncryptedRawData[i].apply(scopes.magneticCardEncryptedRawData[i], arguments);
561 		},
562 		/**
563 		 * This function will be fired when a barcode is successfully read on the LineaDevice. You may attach a listener to this by calling:
564 		 * <pre><code>
565 		 *  LineaBrowser.on('barcodeData', function (barcode, type){
566 		 *      // Your Code
567 		 *  });
568 		 * </code></pre>
569 		 * The first argument is the barcode's data as a string and the second argument is the
570 		 * barcode type as an integer which should correspond to the number in LineaBrowser.BAR_TYPES.*(_EX)?
571 		 * @private
572 		 */
573 		barcodeData: function (){
574 			var len = deligates.barcodeData.length;
575 			for(var i=0;i<len;i++)
576 				deligates.barcodeData[i].apply(scopes.barcodeData[i], arguments);
577 		},
578 		/**
579 		 * This function will be fired when the LineaDevice changes connection state. You may attach a listener to this by calling:
580 		 * <pre><code>
581 		 *  LineaBrowser.on('connectionState', function (state){
582 		 *      // Your Code
583 		 *  });
584 		 * </code></pre>
585 		 * The first parameter is the state corresponding to LineaBrowser.CONN_* for which state it was changed into.
586 		 * @private
587 		 */
588 		connectionState: function (){
589 			var len = deligates.connectionState.length;
590 			for(var i=0;i<len;i++)
591 				deligates.connectionState[i].apply(scopes.connectionState[i], arguments);
592 		},
593 		/**
594 		 * This function will be fired when the LineaDevice reads a credit card. You may attach a listener to this by calling:
595 		 * <pre><code>
596 		 *  LineaBrowser.on('creditCardData', function (accountNumber, cardholderName, experationYear, experationMonth, serviceCode, discretionaryData, firstName, lastName){
597 		 *      // Your Code
598 		 *  });
599 		 * </code></pre>
600 		 * See above for the parameters passed and their names.
601 		 * @private
602 		 */
603 		creditCardData: function (){
604 			var len = deligates.creditCardData.length;
605 			for(var i=0;i<len;i++)
606 				deligates.creditCardData[i].apply(scopes.creditCardData[i], arguments);
607 		}
608 	};
609 }();
610 if(window.onLineaBrowserLoad)
611 	/**
612 	 * This custom function gets called when the the Linea Browser API loads and is ready to send and receive commands.
613 	 * @function
614 	 * @exmple
615 	 * window.onLineaBrowserLoad = function (){
616 	 *	LineaBrowser.playSound(100, [1000, 200, 4000, 100, 100, 500]);
617 	 * };
618 	 */
619 	window.onLineaBrowserLoad();
