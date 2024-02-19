let searchInput = document.getElementById('search_bar')
let searchRes = document.getElementById('search_res')
let suplliersul = document.getElementById('suplliersul')
let arrowdown = document.getElementById('arrow-down')

let drop ='down';
arrowdown.onclick=()=>{
    if(drop=='down'){
        searchRes.style.display='block'
        let tr= suplliersul.getElementsByTagName('tr');
        for(var i=0; i<tr.length; i++){
            let td = tr[i].getElementsByTagName('td')[0];
            td.onclick=()=>{
                    searchInput.value = td.textContent
                searchRes.style.display='none'
            }}
        arrowdown.style.rotate='180deg'
        drop='up';
    }else{
        arrowdown.style.rotate='0deg'
        searchRes.style.display='none'
        drop='down'
    }
}
searchInput.onkeyup=()=>{
    if(searchInput.value!=''){
    searchRes.style.display='block'
    let filter = searchInput.value.toUpperCase();
    let tr= suplliersul.getElementsByTagName('tr');
                for(var i=0; i<tr.length; i++){
                    let td = tr[i].getElementsByTagName('td')[0];
                    td.onclick=()=>{
                        searchInput.value = td.textContent
                        searchRes.style.display='none'
                    }
                    if(td){
                        let txtvalue = td.textContent;
                        if(txtvalue.toLocaleUpperCase().indexOf(filter)>-1){
                            tr[i].style.display='';
                            
                        }else{   
                            tr[i].style.display='none';
                        }
                    }
                    
                }
    }else{searchRes.style.display='none'}
}
