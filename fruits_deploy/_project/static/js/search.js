let tablebody = document.getElementById('tablebody')
let searchbar = document.getElementById('searchbar')
searchbar.onkeyup=()=>{
    let filter = searchbar.value.toUpperCase();
    let tr= tablebody.getElementsByTagName('tr');
                for(var i=0; i<tr.length; i++){
                    let td = tr[i].getElementsByTagName('td')[1];
                    if(td){
                        let txtvalue = td.textContent;
                        if(txtvalue.toLocaleUpperCase().indexOf(filter)>-1){
                            tr[i].style.display='';
                            
                        }else{   
                            tr[i].style.display='none';
                        }
                    }
                }
}