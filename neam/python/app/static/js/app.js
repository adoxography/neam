!function(t){var e={};function o(n){if(e[n])return e[n].exports;var r=e[n]={i:n,l:!1,exports:{}};return t[n].call(r.exports,r,r.exports,o),r.l=!0,r.exports}o.m=t,o.c=e,o.d=function(t,e,n){o.o(t,e)||Object.defineProperty(t,e,{configurable:!1,enumerable:!0,get:n})},o.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return o.d(e,"a",e),e},o.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},o.p="/",o(o.s=0)}([function(t,e,o){o(1),t.exports=o(2)},function(t,e){$(function(){var t={progress_bar:$("#progress-bar"),button:$("#submit-button"),text:$("#info-text")};t.progress_bar.hide(),t.text.hide(),$("#annotation-form").ajaxForm({success:function(e,o,n){status_url=n.getResponseHeader("Location"),function t(e,o){$.getJSON(e,function(n){var r=n.state;"PENDING"==r||"PROGRESS"==r?setTimeout(function(){t(e,o)},2e3):(window.location="/download/"+n.result,o.progress_bar.hide(),o.text.hide(),o.button.removeClass("disabled"))})}(status_url,t)},beforeSubmit:function(){t.progress_bar.show(),t.text.show(),t.button.addClass("disabled")}})})},function(t,e){}]);