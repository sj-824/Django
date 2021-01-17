const typewriter = (param) => {
    let el = document.querySelector(param.el);
    let speed = param.speed;
    let string = param.string.split('');
    console.log(string);
    string.forEach((char,index) => {
        setTimeout(() => {
            el.textContent += char;
        },speed*index);
    });
};

typewriter({
    el: '#title h1',
    string: 'Welcome to AnimEval',
    speed: 50,
});

let loginDisplay = () =>{
    const loginElem = document.getElementById('login');
    document.addEventListener('keypress',(e) => {
        if(e.key === 'Enter') {
            loginElem.classList.add('show');
        }
    })
}

loginDisplay();
