let sellcar = document.getElementById('sellcar')
        sellcar.onclick=()=>{
            window.location.href='sellcar.html'
        }
        let editcarsell = document.getElementById('editcarsell')
        let closesellcon = document.getElementById('closesellcon')
        let editsell = document.getElementById('editsell')
        editsell.onclick=()=>{
            editcarsell.style.display='flex'
        }
        closesellcon.onclick=()=>{
            editcarsell.style.display='none'
        }
        let profits = document.getElementById('profits')
        let closeprofits = document.getElementById('closeprofits')
        let sales = document.getElementById('sales')
        sales.onclick=()=>{
            profits.style.display='flex'
        }
        closeprofits.onclick=()=>{
            profits.style.display='none'
        }
        let loses = document.getElementById('loses')
        let closeloses = document.getElementById('closeloses')
        let deleteoradd = document.getElementById('deleteoradd')
        deleteoradd.onclick=()=>{
            loses.style.display='flex'
        }
        closeloses.onclick=()=>{
            loses.style.display='none'
        }