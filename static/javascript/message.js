'use strict';

const message = document.getElementById('message').textContent;
document.getElementById('message').textContent = '';

let mess = '';
let i = 0;

let typing = () => {
    mess += message.charAt(i);
    document.getElementById('message').textContent = mess;
    i += 1;
    if (i === message.length - 1) {
        clearTimeout(refresh());
    }
    refresh();
}

let refresh = () => {
    setTimeout(typing,100);
}

typing();




// let ChangeOpacity = (Diff) => {
//     let target = document.getElementById('detail1');
//     target.style.opacity = `${Diff / 255}`;
// }

// // let Diff = 0;
// // let ClickFlag = 'False';
// // let update = () => {
// //     if (ClickFlag === 'False') {
// //         Diff += 15;
// //         console.log(ClickFlag);
// //         console.log(Diff); 
// //         if (Diff >= 255) {
// //                 ClickFlag = 'True';
// //             }
// //         if (Diff < 255) {
// //             ChangeColor(Diff);
// //             ChangeOpacity(Diff);
// //             requestAnimationFrame(update);
// //         }
// //     }
// // }

// let Btn1Flag;
// let Btn2Flag;
// let target;
let Diff = 0;

let BtnUpdate = () => {
        Diff += 15;
        console.log(Diff);
        if (Diff < 255) {
            ChangeColor(Diff);
            requestAnimationFrame(BtnUpdate);
        }
    }

function ChangeColor(Diff) {
    if (Btn1Flag === 'False'){
        btn1.style.backgroundColor = `rgba(${Diff},0,0,1)`;
    }
    if (Btn2Flag === 'False'){
        btn2.style.backgroundColor = `rgba(${Diff},0,0,1)`;
    }
    
}

let Btn1ResetColor = () => {
    Diff -= 15;
    if (Diff > 0){
        btn1.style.backgroundColor = `rgba(${Diff},0,0,1)`;
        console.log(Diff);
        requestAnimationFrame(Btn1ResetColor);
        
    }
}
let Btn2ResetColor = () => {
    Diff -= 15;
    if (Diff > 0){
        btn2.style.backgroundColor = `rgba(${Diff},0,0,1)`;
        requestAnimationFrame(Btn2ResetColor);
    }
}
const btn1 = document.getElementById('btn1');
const btn2 = document.getElementById('btn2');
let Btn1Flag;
let Btn2Flag;
let FlagJudge = () => {
    if (Btn1Flag === 'False'){
        // 処理
        console.log('Flag1');
        BtnUpdate();
    }
    if (Btn2Flag === 'False'){
        // 処理
        BtnUpdate();
    }
}

let FlagClear = () => {
    console.log('FlagClear');
    if(Btn1Flag === 'False'){
    Btn1ResetColor();
    Btn1Flag = 'True';
    Btn2Flag = 'True';
    }
    if(Btn2Flag === 'False'){
    Btn2ResetColor();
    Btn1Flag = 'True';
    Btn2Flag = 'True';
    }
}


document.getElementById('btn1').addEventListener('click',(e) => {
    e.stopPropagation();
    console.log(Btn2Flag);
    if (Btn2Flag === 'False'){
        Btn2ResetColor();
    }
    Btn1Flag = 'False';
    Btn2Flag = 'True';
    FlagJudge();
    
},false)

document.getElementById('btn2').addEventListener('click',(e) => {
    e.stopPropagation();
    if (Btn1Flag === 'False'){
        Btn1ResetColor();
        console.log('reset');
    }
    Btn1Flag = 'True';
    Btn2Flag = 'False';
    Diff = 0;
    if (Diff <= 0){
    FlagJudge();
    console.log('end')
    }
    console.log('end');
},false)
document.getElementById('wrapper').addEventListener('click',FlagClear,false);





