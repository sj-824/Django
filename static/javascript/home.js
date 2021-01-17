'use strict';

const targetElem = document.querySelectorAll('#content');
const targetCount = targetElem.length;

for (let i = 0; i < targetCount; i++){
    let reviewContent = targetElem[i].textContent;
    if (reviewContent.includes('ネタバレ')) {
        targetElem[i].textContent = '※ネタバレを含む';
        targetElem[i].style.fontWeight = '900';

    }
}

function detail(list,count){
    for (let i = 0; i<targetCount; i++){
        let displayContent = targetElem[i].textContent.substr(0,100);
        let remainContent = targetElem[i].textContent.substr(100);
        if (displayContent.includes('ネタバレを含む') === false){
            if (remainContent != ''){
                targetElem[i].textContent = displayContent;
                targetElem[i].nextElementSibling.style.display = 'block';
            } else {
                targetElem[i].nextElementSibling.style.display = 'none';
            }
        }
    }
}

detail(targetElem,targetCount);