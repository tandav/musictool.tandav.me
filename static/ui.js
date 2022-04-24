// window.addEventListener('scroll',(event) => {
//     console.log('Scrolling...');
// });

// window.onscroll = function(event) {
//     console.log('Scrolling...');
// };
//     document.onscroll = function() { console.log('Works in Chrome!'); };

document.addEventListener('keydown', (event) => {
    const keyName = event.key
    if (keyName === 'ArrowUp') {
      window.location = "http://0.0.0.0:8001/diads/lowest_up";
      console.log('up')
    }
    else if (keyName === 'ArrowDown') {
        window.location = "http://0.0.0.0:8001/diads/lowest_down";
        console.log('down')
    }
})
