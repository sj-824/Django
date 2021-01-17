'use strict';

const targetElem = document.querySelectorAll('#content');
const targetCount = targetElem.length;

function detail(list,count){
    for (let i = 0; i<targetCount; i++){
        let displayContent = targetElem[i].textContent.substr(0,100);
        let remainContent = targetElem[i].textContent.substr(100);
        console.log(remainContent);
        if (remainContent != ''){
            targetElem[i].textContent = displayContent;
        }
    }
}

detail(targetElem,targetCount);