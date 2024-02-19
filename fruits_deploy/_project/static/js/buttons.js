let addkind= document.getElementById('addkind')
let kinds= document.getElementById('kinds')
let closekinds = document.getElementById('closekinds')
let editcar = document.getElementById('editcar');
let editcarcon = document.getElementById('editcarcon');
let closeeditcon = document.getElementById('closeeditcon')
addkind.onclick=()=>{
    kinds.style.display='flex';
}
closekinds.onclick=()=>{
    kinds.style.display='none';
}
editcar.onclick=()=>{
    editcarcon.style.display='flex';
}
closeeditcon.onclick=()=>{
    editcarcon.style.display='none'
}
