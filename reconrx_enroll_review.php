<?php

#error_reporting(-1);
#ini_set('display_errors', 'On');

include 'includes/mysql.php';
include 'includes/admin_usercheck.php';
include 'includes/log_activity.php';
$db    = 'officedb'; 
$table = 'pharmacy'; 

### Is this an admin mode review?
  $user = $_COOKIE["LOGIN"];

if (isset($_POST['admin_ncpdp'])) { $admin_ncpdp = $_POST['admin_ncpdp']; } else { $admin_ncpdp = ""; }
if (isset($_POST['admin_npi'])) { $admin_npi = $_POST['admin_npi']; } else { $admin_npi = ""; }
if (isset($_POST['admin_id'])) { $admin_id = $_POST['admin_id']; } else { $admin_id = ""; }
if (isset($_POST['new_ncpdp'])) { $new_ncpdp = $_POST['new_ncpdp']; } else { $new_ncpdp = ""; }
if (isset($_POST['coo_date']))  { $coo_date = $_POST['coo_date'];  } else { $coo_date = ""; }
if (isset($_POST['arete_service_level']))  {$service_level = $_POST['arete_service_level'];  } else { $service_level = ""; }
if ($admin_ncpdp > 0 && $admin_npi > 0 && $user != "") {
   $returning_ncpdp = $admin_ncpdp;
   $returning_npi   = $admin_npi;
   $admin_mode = 1;
} else if (isset($_COOKIE["cont1"]) && isset($_COOKIE["cont2"])) {
   $returning_ncpdp = $_COOKIE["cont1"];
   $returning_npi   = $_COOKIE["cont2"];
} else {
   echo "No pharmacy info detected, exiting.\n";
   exit();
}

###GATHER POST DATA################################################
$all_post = "";
foreach ($_POST as $param_name => $param_val) {
   if (isset($param_val) && $param_val != "") {
      #echo "Param: $param_name; Value: $param_val<br />\n";
      $$param_name = $param_val;
      $all_post .= "$param_name: $param_val, ";
   } else {
      $$param_name = "";
   }
}
$all_post = rtrim($all_post, ', ');
###################################################################

###READ VALUES FROM DB#############################################
$sql = "
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA='reconrxdb' && TABLE_NAME='enrollment';
";
if ($pull = $mysqli->prepare("$sql")) {
   $pull->execute();
   $all_data = $pull->get_result();
    while ($row = $all_data->fetch_assoc()) {
      $field = $row['COLUMN_NAME'];
      $sqlx = "SELECT $field FROM reconrxdb.enrollment WHERE id = ?";
      if ($value_pull = $mysqli->prepare("$sqlx")) {
         $value_pull->bind_param('i', $admin_id);
         $value_pull->execute();
         $single_field_data = $value_pull->get_result();
         while ($row2 = $single_field_data->fetch_assoc()) {
            #$efield = str_replace('rrx', 'pull', $field);
            $efield = $field;
            $$efield = $row2["$field"];
            # echo "efield: $efield = ". $row2["$field"] . "<br />";
         }
      }
    }
}
###################################################################
#
##$sql = "
##         SELECT  a.Arete_Type
##           FROM $db.$table a
##          WHERE a.NCPDP = ?
##            && Status_ReconRx IS NOT NULL
##       ";
##if ($pull = $mysqli->prepare("$sql")) {
##   $pull->bind_param('i', $rrx_ncpdp);
##   $pull->execute();
##   $checkstore = $pull->get_result();
##   while ($row = $checkstore->fetch_assoc()) {
     if($rrx_service_level) {
       $service_level_disable = 'disabled';
     }
##   }
##   $pull->close();
##  }

$checked = '';


if ($COO) {
  $checked = 'checked';
}
else {
  $coo_date = null;
  $display = '"display:none;"';
}

if($rrx_eoy) {
  $piece = explode("-", $rrx_eoy);
  $eoy_fmt = "$piece[1]/$piece[2]/$piece[0]";
}

if($coo_date) {
  $piece = explode("-", $coo_date);
  $coo_fmt = "$piece[1]$piece[2]$piece[0]";
}
if ($admin_mode == 1 && $coo_date) {
  $disabled = 'disabled';
}
if ($rrx_psao != 'AlignRx') {
  $service_level_disable = 'disabled';
}

if ($admin_mode > 0 && $paidesktop == 'true') {
   #Set conditional/static variables

   $status = "Pending";
   $type   = "ReconRx";

   $rrx_main_address    = $rrx_main_address1    . " " . $rrx_main_address2;
   $rrx_mailing_address = $rrx_mailing_address1 . " " . $rrx_mailing_address2;
   
   $rrx_single_pay = "No";
   
   $rrx_affiliate_name = '';
   $rrx_billing = '';
   $rrx_fee     = '175.00';

   if (preg_match("/GeriMed/i", $rrx_affiliate)) {
     $rrx_fee     = '150.00';
   }

   if (preg_match("/ComputerRx|Rx30/i", $rrx_swvendor)) {
     $rrx_fee     = '125.00';
   }
   $plantype = 'P';


   if ($submit == 'Import to Desktop') {
     if ($insert = $mysqli->prepare("
       INSERT INTO officedb.entity_ids 
        SET description = ?,
        type            = ?
       ;")) 
     {
       $insert->bind_param('is',
         $admin_ncpdp,
         $plantype 
       );
  
       $insert->execute();
     }

     if ($pull = $mysqli->prepare("SELECT LAST_INSERT_ID()")) {
      $pull->execute();
      $ins = $pull->get_result();
      $rec = $ins->fetch_array();
      $admin_pharmacy_id = $rec[0];
      $pull->close();
     } else {
        printf("Prepared Statement Error: %s\n", $mysqli->error);
     }
   }

   if (preg_match("/morris/i", $rrx_wholesaler)) {
	   $rrx_affiliate_name = $rrx_wholesaler;
	   $rrx_billing = "Affiliate";
   } else {
       $rrx_affiliate_name = "Independent";
       $rrx_billing = "Direct/EFT";
   }

   if (preg_match("/Guaranteed Returns|Ontime Soft|GeriMed|Onpoint/i", $rrx_affiliate)) {
     $rrx_affiliate_name = "$rrx_affiliate";
     $rrx_billing = "Direct/EFT";
   }
   
   $rrx_central_pay_835 = '';
   $rrx_central_pay_org = '';
   if (preg_match("/Elevate/i", $rrx_psao) || 
       preg_match("/Cardinal/i", $rrx_psao) || 
       preg_match("/AlignRx/i", $rrx_psao) || 
       preg_match("/GeriMed/i", $rrx_psao) || 
       preg_match("/Health Mart Atlas/i", $rrx_psao) ) {
          $rrx_central_pay_835 = "Yes";
          $rrx_central_pay_org = $rrx_psao;
   } else {
          $rrx_central_pay_835 = "No";
	  $rrx_central_pay_org = "N/A";
   }

   if ($submit == 'Import to Desktop') {
     #### INSERT INTO WEBLOGIN LOGIC
     $success = 0;
     $sql = "SELECT id
               FROM officedb.weblogin
                 WHERE login = '$rrx_login'";
     $result = $mysqli->query($sql);

     if ($result->num_rows > 0) {
       while($row = $result->fetch_assoc()) {
         $login_id = $row["id"];

	 $ins_sql = "INSERT INTO officedb.weblogin_dtl (login_id, pharmacy_id, program)
                     VALUES ('$login_id', '$admin_pharmacy_id', 'ReconRx')";
       }
     } else {
         $ins_sql = "INSERT INTO officedb.weblogin (login, password, type, access, programs, comments, permission_level, display_in_menus)
                     VALUES ('$rrx_login', AES_ENCRYPT('$rrx_password','PAI20181217!'), 'User', '$admin_pharmacy_id', 'ReconRx', '', 'NONE', 'No')";
     }

     if ($mysqli->query($ins_sql) === TRUE) {
       $success = 1;
     } else {
       $err_msg = "Error Inserting Record: " . $mysqli->error;;
     }	     

     if(!$service_level){
       $service_level = NULL; 
     }
     if($COO) {
       $table = 'pharmacy_coo';
     }
     else {
       $coo_date = NULL;
     }
     if ($insert = $mysqli->prepare("
       INSERT INTO $db.$table SET
       Pharmacy_Name = ?,
       NCPDP = ?,
       NPI = ?,
       Status = ?,
       Status_ReconRx = ?,
       Type = ?,
       Legal_Name = ?,
       Medicaid_Primary_Num = ?,
       Medicaid_Primary_State = ?,
       Fed_Tax_Classification = ?,
       FEIN = ?,
       Affiliate_Name = ?,
       EOY_Report_Date = ?,
       Business_Phone = ?,
       Fax_Number = ?,
       Store_User = ?,
       Store_Pass = ?,
       Email_Address = ?,
       Comm_Pref = ?,
       Address = ?,
       City = ?,
       State = ?,
       Zip = ?,
       County = ?,
       Mailing_Address = ?,
       Mailing_City = ?,
       Mailing_State = ?,
       Mailing_Zip = ?,
       Primary_Switch = ?,
       Secondary_Switch = ?,
       Software_Vendor = ?,
       Current_PSAO = ?,
       Billing = ?,
       Single_Pay = ?,
       CentralPay835 = ?,
       CentralPayOrg = ?,
       ReconRx_Fee = ?,
       Pharmacy_ID = ?,
       Arete_Type = ?,
       COO_Date    = ?  ;")) {
       $insert->bind_param('siissssssssssssssssssssssssssssssssssiss',
       $rrx_pharmname,
       $rrx_ncpdp,
       $rrx_npi,
       $status,
       $status,
       $type,
       $rrx_legalname,
       $rrx_medicaid,
       $rrx_main_state,
       $rrx_fed_tax_class,
       $rrx_fed_tax_id,
       $rrx_affiliate_name,
       $rrx_eoy,
       $rrx_phone,
       $rrx_fax,
       $rrx_login,
       $rrx_password,
       $rrx_email,
       $rrx_comm_pref,
       $rrx_main_address,
       $rrx_main_city,
       $rrx_main_state,
       $rrx_main_zip,
       $rrx_main_county_parish,
       $rrx_mailing_address,
       $rrx_mailing_city,
       $rrx_mailing_state,
       $rrx_mailing_zip,
       $rrx_switch,
       $rrx_switch_secondary,
       $rrx_swvendor,
       $rrx_psao,
       $rrx_billing,
       $rrx_single_pay,
       $rrx_central_pay_835,
       $rrx_central_pay_org,
       $rrx_fee,
       $admin_pharmacy_id,
       $service_level,
       $coo_date
       );

       $insert->execute();

       #Use for debugging confusing SQL problems
       $myFile = "errors_confused.txt";
       $fh = fopen($myFile, 'w') or die("can't open file2");
       fwrite($fh, $mysqli->error);
        fclose($fh);
       echo $mysqli->error;

       $insert->close();

       $action = "$rrx_ncpdp sent to PAI Desktop";
       log_activity($user, $action, null);
     } else {
       printf("Prepared Statement Error:$db %s\n", $mysqli->error);
       $myFile = "errors.txt";
       $fh = fopen($myFile, 'w') or die("can't open file3");
       fwrite($fh, $mysqli->stmt);
       fclose($fh);
     }
   }
   elseif ($submit == 'Update Desktop') {
     #### UPDATE WEBLOGIN LOGIC
     $success = 0;
     $upd_sql = "UPDATE officedb.weblogin_dtl 
		    SET program = CONCAT(program,':', 'ReconRx')
		  WHERE pharmacy_id = '$admin_pharmacy_id'
                    AND program NOT LIKE '%ReconRx%'";

     if ($mysqli->query($upd_sql) === TRUE) {
       $success = 1;
     } else {
       $err_msg = "Error Updating Record: " . $mysqli->error;;
     }

     if($service_level != 'NULL'){
       $service_level = "'$service_level'";
     }

     if (!in_array($service_level, ['B','E'])) {
       $service_level = 'NULL'; 
     }

     $new_name = str_replace('\'', '\\\'', $rrx_pharmname);

     $upd_sql = "
       UPDATE officedb.pharmacy 
          SET 
       Pharmacy_Name =
         CASE 
           WHEN Pharmacy_Name IS NULL THEN '$new_name'
           ELSE Pharmacy_Name
         END,
       Status = 
         CASE 
           WHEN Status IS NULL THEN '$status'
           ELSE Status
         END,
       Status_ReconRx = 
         CASE 
           WHEN Status_ReconRx IS NULL THEN '$status'
           ELSE Status_ReconRx
         END,
       Type = 
         CASE 
           WHEN Type IS NULL THEN '$type'
           ELSE CONCAT(Type,':', 'ReconRx')
         END,
       Legal_Name =
         CASE 
           WHEN Legal_Name IS NULL THEN '$rrx_legalname'
           ELSE Legal_Name
         END,
       Medicaid_Primary_Num =
         CASE 
           WHEN Medicaid_Primary_Num IS NULL THEN '$rrx_medicaid'
           ELSE Medicaid_Primary_Num
         END,
       Medicaid_Primary_State =
         CASE 
           WHEN Medicaid_Primary_State IS NULL THEN '$rrx_main_state'
           ELSE Medicaid_Primary_State
         END,
       Fed_Tax_Classification =
         CASE 
           WHEN Fed_Tax_Classification IS NULL THEN '$rrx_fed_tax_class'
           ELSE Fed_Tax_Classification
         END,
       FEIN =
         CASE 
           WHEN FEIN IS NULL THEN '$rrx_fed_tax_id'
           ELSE FEIN
         END,
       Affiliate_Name =
         CASE 
           WHEN Affiliate_Name IS NULL THEN '$rrx_affiliate_name'
           ELSE Affiliate_Name
         END,
       EOY_Report_Date =
         CASE 
           WHEN EOY_Report_Date IS NULL THEN '$rrx_eoy'
           ELSE EOY_Report_Date
         END,
       Business_Phone =
         CASE 
           WHEN Business_Phone IS NULL THEN '$rrx_phone'
           ELSE Business_Phone
         END,
       Fax_Number =
         CASE 
           WHEN Fax_Number IS NULL THEN '$rrx_fax'
           ELSE Fax_number
         END,
       Email_Address =
         CASE 
           WHEN Email_Address IS NULL THEN '$rrx_email'
           ELSE Email_Address
         END,
       Comm_Pref =
         CASE 
           WHEN Comm_Pref IS NULL THEN '$rrx_comm_pref'
           ELSE Comm_Pref
         END,
       Address =
         CASE 
           WHEN Address IS NULL THEN '$rrx_main_address'
           ELSE Address
         END,
       City =
         CASE 
           WHEN City IS NULL THEN '$rrx_main_city'
           ELSE City
         END,
       State =
         CASE 
           WHEN State IS NULL THEN '$rrx_main_state'
           ELSE State
         END,
       Zip =
         CASE 
           WHEN Zip IS NULL THEN '$rrx_main_zip'
           ELSE Zip
         END,
       County =
         CASE 
           WHEN County IS NULL THEN '$rrx_main_county_parish'
           ELSE County
         END,
       Mailing_Address =
         CASE 
           WHEN Mailing_Address IS NULL THEN '$rrx_mailing_address'
           ELSE Mailing_Address
         END,
       Mailing_City =
         CASE 
           WHEN Mailing_City IS NULL THEN '$rrx_mailing_city'
           ELSE Mailing_City
         END,
       Mailing_State =
         CASE 
           WHEN Mailing_State IS NULL THEN '$rrx_mailing_state'
           ELSE Mailing_State
         END,
       Mailing_Zip =
         CASE 
           WHEN Mailing_Zip IS NULL THEN '$rrx_mailing_zip'
           ELSE Mailing_Zip
         END,
       Primary_Switch =
         CASE 
           WHEN Primary_Switch IS NULL THEN '$rrx_switch'
           ELSE Primary_Switch
         END,
       Secondary_Switch =
         CASE 
           WHEN Secondary_Switch IS NULL THEN '$rrx_switch_secondary'
           ELSE Secondary_Switch
         END,
       Software_Vendor =
         CASE 
           WHEN Software_Vendor IS NULL THEN '$rrx_swvendor'
           ELSE Software_Vendor
         END,
       Current_PSAO =
         CASE 
           WHEN Current_PSAO IS NULL THEN '$rrx_psao'
           ELSE Current_PSAO
         END,
       Billing =
         CASE 
           WHEN Billing IS NULL THEN '$rrx_billing'
           ELSE Billing
         END,
       Single_Pay =
         CASE 
           WHEN Single_Pay IS NULL THEN '$rrx_single_pay'
           ELSE Single_Pay
         END,
       CentralPay835 =
         CASE 
           WHEN CentralPay835 IS NULL THEN '$rrx_central_pay_835'
           ELSE CentralPay835
         END,
       CentralPayOrg =
         CASE 
           WHEN CentralPayOrg IS NULL THEN '$rrx_central_pay_org'
           ELSE CentralPayOrg
         END,
       ReconRx_Fee =
         CASE 
           WHEN ReconRx_Fee IS NULL THEN '$rrx_fee'
           ELSE ReconRx_Fee
	 END,
       Arete_Type = $service_level
         WHERE NCPDP = '$rrx_ncpdp'
            && NPI = '$rrx_npi'
            && type NOT LIKE '%ReconRx%'
     ;";

       if ($mysqli->query($upd_sql) === TRUE) {
         $success = 1;
       } else {
         $success = 0;
         $err_msg .= "Error Updating Pharmacy Record: " . $upd_sql . ' : ' . $mysqli->error;
       }       

       ##Use for debugging confusing SQL problems
       #$myFile = "errors_confused.txt";
       #$fh = fopen($myFile, 'w') or die("can't open file");
       #fwrite($fh, $mysqli->error);
       #fclose($fh);
       #echo $mysqli->error;

       $action = "$rrx_ncpdp sent to PAI Desktop";
       log_activity($user, $action, null);
   }
   
   ####################
   # Insert Contact Data
       
   if ($admin_pharmacy_id != '') {
     add_contact($mysqli, $admin_pharmacy_id, '11', $rrx_owner_contact_name, '', $rrx_owner_contact_email, $rrx_owner_contact_phone, $rrx_owner_contact_cell, '');
     add_contact($mysqli, $admin_pharmacy_id, '12', $rrx_main_contact_name, $rrx_main_contact_title, $rrx_main_contact_email, $rrx_main_contact_phone, $rrx_main_contact_cell, $rrx_main_contact_fax);
     add_contact($mysqli, $admin_pharmacy_id, '17', $rrx_auth_contact_name, $rrx_auth_contact_title, $rrx_auth_contact_email, $rrx_auth_contact_phone, '', $rrx_auth_contact_fax);
     add_contact($mysqli, $admin_pharmacy_id, '39', $rrx_auth_contact_res_name, $rrx_auth_contact_res_title, $rrx_auth_contact_res_email, $rrx_auth_contact_res_phone, '', $rrx_auth_contact_res_fax);
     add_contact($mysqli, $admin_pharmacy_id, '40', $rrx_auth_contact_pmt_name, $rrx_auth_contact_pmt_title, $rrx_auth_contact_pmt_email, $rrx_auth_contact_pmt_phone, '', $rrx_auth_contact_pmt_fax);
   }
   else {
      echo "Error detected: Please try again later";
   }

   ####################
}

if ($admin_mode > 0 && $archive == 'true') {
	if ($update = $mysqli->prepare("
	  UPDATE reconrxdb.enrollment 
	  SET rrx_status = 'archive' 
	  WHERE 
	  id = ?
	  ;")) {
	  $update->bind_param('i',
	  $id
	  );

		$update->execute();

		#Use for debugging confusing SQL problems
		#$myFile = "errors_confused.txt";
		#$fh = fopen($myFile, 'w') or die("can't open file");
		#fwrite($fh, $mysqli->error);
		#fclose($fh);
		#echo $mysqli->error;

		$update->close();
		
		$rrx_status = 'archive';

		$action = "$rrx_ncpdp enrollment archived.";
		log_activity($user, $action, null);
		
		header('Location: admin.php');
		exit();
	 } else {
		printf("Prepared Statement Error: %s\n", $mysqli->error);
		$myFile = "errors.txt";
		$fh = fopen($myFile, 'w') or die("can't open file4");
		fwrite($fh, $mysqli->error);
		fclose($fh);
	 }
}

?>

<!-- Header and Navigation------------------------------------------ -->
<!doctype html> 
<html lang="en">
<?php include 'includes/header_nav.php'; ?>
<div id="wrapper"><!-- wrapper -->
<div id="content_container_front">
<div id="mainbody_front">
<!-- --------------------------------------------------------------- -->

<div class="rrx-two-column-wrapper clear">
<?php
if ($submit == 'Import to Desktop' || $submit == 'Update Desktop' && $success == 0) {
   echo "<p><strong>$err_msg</strong>";
}
?>
</div> <!-- end rrx-two-column-wrapper -->

<?php #echo "$upd_sql<br>"; ?>

<div class="rrx-two-column-wrapper">

<div class="rrx-two-column">

   <div class="field_title"> </div>
   <h1>Pharmacy Information</h1>
   <br>
   <div class="field_title">NCPDP</div>
   <INPUT class="rrx-input-text-form required ncpdp" TYPE="text" NAME="rrx_ncpdp" VALUE="<?php echo $rrx_ncpdp; ?>" disabled>

   <div class="field_title">Pharmacy Name</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_pharmname" VALUE="<?php echo $rrx_pharmname; ?>" disabled>

   <div class="field_title">Pharmacy Legal Name</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_legalname" VALUE="<?php echo $rrx_legalname; ?>" disabled>

   <div class="field_title">Federal Tax Class</div>
   <select name="rrx_fed_tax_class" class="rrx-dropdown-form required" disabled>
   <option value="<?php echo $rrx_fed_tax_class; ?>" selected><?php echo $rrx_fed_tax_class; ?></option>
   <option value="C-Corp">C-Corp</option>
   <option value="LLC">LLC</option>
   <option value="Non Profit/Exempt">Non Profit/Exempt</option>
   <option value="Partnership">Partnership</option>
   <option value="S-Corp">S-Corp</option>
   <option value="Sole Proprietor">Sole Proprietor</option>
   </select>

   <div class="field_title">Medicaid Number</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_medicaid" VALUE="<?php echo $rrx_medicaid; ?>" disabled>

   <div class="field_title">Software Vendor</div>
   <select name="rrx_swvendor" id="swvendor" class="rrx-dropdown-form swvendor required" disabled>
   <?php 
   if ($rrx_swvendor == "") {
      echo "<option value=\"\" selected></option>";
   } else {
      echo "<option value=\"$rrx_swvendor\" selected>$rrx_swvendor</option>";
   }
   ?>
   <!-- 
   <option value="QS1">QS1</option>
   <option value="Rx30">Rx30</option>
   <option value="Pioneer">Pioneer</option>
   <option value="Prism">Prism</option>
   <option value="SpeedScript">SpeedScript</option>
   <option value="Other">Other</option>
   -->
   </select>

   <div id="otherType" style="display:none;">
   <div class="field_title">Other Software Vendor</div>
   <INPUT TYPE="text" NAME="rrx_swvendor_other" class="rrx-input-text-form swvendor_other" VALUE="<?php echo $rrx_swvendor_other; ?>" disabled>
   </div>

   <div class="field_title">Drug Wholesaler</div>
   <select name="rrx_wholesaler" class="rrx-dropdown-form swvendor required" disabled>
   <?php 
   if ($rrx_wholesaler == "") {
      echo "<option value=\"\" selected></option>";
   } else {
      echo "<option value=\"$rrx_wholesaler\" selected>$rrx_wholesaler</option>";
   }

   ?>
   </select>

   <div class="field_title">End of your current Fiscal Year</div>
   <INPUT class="rrx-input-text-form datepicker required" TYPE="text" NAME="rrx_eoy" VALUE="<?php echo $eoy_fmt; ?>" disabled>


</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

   <div class="field_title" style="padding-bottom: 55px "> </div>

   <div class="field_title" style="margin-top: 10px;">NPI</div>
   <INPUT class="rrx-input-text-form required npi" TYPE="text" NAME="rrx_npi" VALUE="<?php echo $rrx_npi; ?>" disabled>

   <div class="field_title">Federal Tax ID</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_fed_tax_id" VALUE="<?php echo $rrx_fed_tax_id; ?>" disabled>

   <div class="field_title">Switch Company (Primary)</div>
   <select name="rrx_switch" class="rrx-dropdown-form swvendor required" disabled>
   <?php 
   if ($rrx_switch == "") {
      echo "<option value=\"\" selected></option>";
   } else {
      echo "<option value=\"$rrx_switch\" selected>$rrx_switch</option>";
   }

   ?>
   </select>

   <div class="field_title">Switch Company (Secondary)</div>
   <select name="rrx_switch_secondary" class="rrx-dropdown-form swvendor required" disabled>
   <?php 
   if ($rrx_switch_secondary == "") {
      echo "<option value=\"\" selected></option>";
   } else {
      echo "<option value=\"$rrx_switch_secondary\" selected>$rrx_switch_secondary</option>";
   }
   ?>
   </select>

   <div class="field_title">Current PSAO</div>
   <select id = "rrx_psao" name="rrx_psao" class="rrx-dropdown-form swvendor required" disabled>
   <?php 
   if ($rrx_psao == "") {
      echo "<option value=\"\" selected></option>";
   } else {
      echo "<option value=\"$rrx_psao\" selected>$rrx_psao</option>";
   }
   ?>
   </select><br>
   <input type="radio" id = "rrx_service_levelB" name="service_level" value="B" onchange="assign_service(this.value)" <?php if ($rrx_service_level == 'B') { echo ' checked '; } echo $service_level_disable ?> > Enhanced 
   <input type="radio" id = "rrx_service_levelE" name="service_level" value="E" onchange="assign_service(this.value)" <?php if ($rrx_service_level == 'E') { echo ' checked '; } echo $service_level_disable ?> > Enhanced Plus

</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

<hr class="clear" /><br />

<div class="rrx-two-column-wrapper">
<div class="rrx-two-column">

   <div class="field_title">Phone (Pharmacy)</div>
   <INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_phone" VALUE="<?php echo $rrx_phone; ?>" disabled>

   <div class="field_title">Fax (Pharmacy)</div>
   <INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_fax" VALUE="<?php echo $rrx_fax; ?>" disabled>

</div> <!-- rrx-two-column -->
<div class="rrx-two-column">

   <div class="field_title">Email (Pharmacy)</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_email" VALUE="<?php echo $rrx_email; ?>" disabled>

   <div class="field_title">Communication Preference</div>
   <select name="rrx_comm_pref" class="rrx-dropdown-form required" disabled>
   <?php if ($rrx_comm_pref == "") {
      echo "<option value=\"\" selected></option>";
   } else {
      echo "<option value=\"$rrx_comm_pref\" selected>$rrx_comm_pref</option>";
   } ?>
   <!-- <option value=""></option> -->
   <option value="Email">Email</option>
   <option value="Fax">Fax</option>
   <option value="Both">Both</option>
   </select>

</div> <!-- rrx-two-column -->
</div> <!-- end rrx-two-column-wrapper -->

<hr class="clear" />

<h1>Login</h1>

<div class="rrx-two-column-wrapper">

<div class="rrx-two-column">

		<div class="field_title">User Name</div>
		<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_login" VALUE="<?php echo $rrx_login; ?>" disabled>
	
</div> <!-- rrx-two-column -->
<div class="rrx-two-column">

		<div class="field_title">Password</div>
		<INPUT class="rrx-input-text-form required" TYPE="password" NAME="rrx_password" VALUE="<?php echo $rrx_password; ?>" disabled>
		

</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

		<p>* These will be the credentials used to login to our website once your agreement is processed and pharmacy made active.</p>

<hr class="clear" />

<h1>Pharmacy Address</h1>

<div class="rrx-two-column-wrapper">

<div class="rrx-two-column">

   <h2>Physical Address</h2>

   <div class="field_title">Address Line 1</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_main_address1" VALUE="<?php echo $rrx_main_address1; ?>" disabled>

   <div class="field_title">Address Line 2</div>
   <INPUT class="rrx-input-text-form" TYPE="text" NAME="rrx_main_address2" VALUE="<?php echo $rrx_main_address2; ?>" disabled>

   <div class="field_title">City</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_main_city" VALUE="<?php echo $rrx_main_city; ?>" disabled>

   <div class="field_title">State</div>
   <select name="rrx_main_state" class="rrx-dropdown-form required" disabled>
   <?php if ($rrx_main_state == "") {
      echo "<option value=\"\" selected></option>";
   } else {
      echo "<option value=\"$rrx_main_state\" selected>$rrx_main_state</option>";
   } ?>
   <option value="AL">AL</option>
   <option value="AK">AK</option>
   <option value="AZ">AZ</option>
   <option value="AR">AR</option>
   <option value="CA">CA</option>
   <option value="CO">CO</option>
   <option value="CT">CT</option>
   <option value="DE">DE</option>
   <option value="DC">DC</option>
   <option value="FL">FL</option>
   <option value="GA">GA</option>
   <option value="HI">HI</option>
   <option value="ID">ID</option>
   <option value="IL">IL</option>
   <option value="IN">IN</option>
   <option value="IA">IA</option>
   <option value="KS">KS</option>
   <option value="KY">KY</option>
   <option value="LA">LA</option>
   <option value="ME">ME</option>
   <option value="MD">MD</option>
   <option value="MA">MA</option>
   <option value="MI">MI</option>
   <option value="MN">MN</option>
   <option value="MS">MS</option>
   <option value="MO">MO</option>
   <option value="MT">MT</option>
   <option value="NE">NE</option>
   <option value="NV">NV</option>
   <option value="NH">NH</option>
   <option value="NJ">NJ</option>
   <option value="NM">NM</option>
   <option value="NY">NY</option>
   <option value="NC">NC</option>
   <option value="ND">ND</option>
   <option value="OH">OH</option>
   <option value="OK">OK</option>
   <option value="OR">OR</option>
   <option value="PA">PA</option>
   <option value="RI">RI</option>
   <option value="SC">SC</option>
   <option value="SD">SD</option>
   <option value="TN">TN</option>
   <option value="TX">TX</option>
   <option value="UT">UT</option>
   <option value="VT">VT</option>
   <option value="VA">VA</option>
   <option value="WA">WA</option>
   <option value="WV">WV</option>
   <option value="WI">WI</option>
   <option value="WY">WY</option>
   </select>

   <div class="field_title">Zip</div>
   <INPUT class="rrx-input-text-form required zip" TYPE="text" NAME="rrx_main_zip" VALUE="<?php echo $rrx_main_zip; ?>" disabled>

   <div class="field_title">County or Parish</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_main_county_parish" VALUE="<?php echo $rrx_main_county_parish; ?>" disabled>

</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

   <h2>Mailing Address</h2>


   <div class="field_title">Address Line 1</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_mailing_address1" VALUE="<?php echo $rrx_mailing_address1; ?>" disabled>

   <div class="field_title">Address Line 2</div>
   <INPUT class="rrx-input-text-form" TYPE="text" NAME="rrx_mailing_address2" VALUE="<?php echo $rrx_mailing_address2; ?>" disabled>

   <div class="field_title">City</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_mailing_city" VALUE="<?php echo $rrx_mailing_city; ?>" disabled>

   <div class="field_title">State</div>
   <select name="rrx_mailing_state" class="rrx-dropdown-form required" disabled>
   <?php if ($rrx_mailing_state == "") {
      echo "<option value=\"\" selected></option>";
   } else {
      echo "<option value=\"$rrx_mailing_state\" selected>$rrx_mailing_state</option>";
   } ?>
   <option value="AL">AL</option>
   <option value="AK">AK</option>
   <option value="AZ">AZ</option>
   <option value="AR">AR</option>
   <option value="CA">CA</option>
   <option value="CO">CO</option>
   <option value="CT">CT</option>
   <option value="DE">DE</option>
   <option value="DC">DC</option>
   <option value="FL">FL</option>
   <option value="GA">GA</option>
   <option value="HI">HI</option>
   <option value="ID">ID</option>
   <option value="IL">IL</option>
   <option value="IN">IN</option>
   <option value="IA">IA</option>
   <option value="KS">KS</option>
   <option value="KY">KY</option>
   <option value="LA">LA</option>
   <option value="ME">ME</option>
   <option value="MD">MD</option>
   <option value="MA">MA</option>
   <option value="MI">MI</option>
   <option value="MN">MN</option>
   <option value="MS">MS</option>
   <option value="MO">MO</option>
   <option value="MT">MT</option>
   <option value="NE">NE</option>
   <option value="NV">NV</option>
   <option value="NH">NH</option>
   <option value="NJ">NJ</option>
   <option value="NM">NM</option>
   <option value="NY">NY</option>
   <option value="NC">NC</option>
   <option value="ND">ND</option>
   <option value="OH">OH</option>
   <option value="OK">OK</option>
   <option value="OR">OR</option>
   <option value="PA">PA</option>
   <option value="RI">RI</option>
   <option value="SC">SC</option>
   <option value="SD">SD</option>
   <option value="TN">TN</option>
   <option value="TX">TX</option>
   <option value="UT">UT</option>
   <option value="VT">VT</option>
   <option value="VA">VA</option>
   <option value="WA">WA</option>
   <option value="WV">WV</option>
   <option value="WI">WI</option>
   <option value="WY">WY</option>
   </select>

   <div class="field_title">Zip</div>
   <INPUT class="rrx-input-text-form required zip" TYPE="text" NAME="rrx_mailing_zip" VALUE="<?php echo $rrx_mailing_zip; ?>" disabled>

   <div class="field_title">County or Parish</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_mailing_county_parish" VALUE="<?php echo $rrx_mailing_county_parish; ?>" disabled>

</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

<hr class="clear" />

<h1>Owner Contact Information</h1>

<div class="rrx-two-column-wrapper">

<div class="rrx-two-column">

	<div class="field_title">Owner Name (Full)</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_owner_contact_name" VALUE="<?php echo $rrx_owner_contact_name; ?>" disabled>
	
</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

	<div class="field_title">Owner Contact Phone</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_owner_contact_phone" VALUE="<?php echo $rrx_owner_contact_phone; ?>" disabled>

	<div class="field_title">Owner Contact Cell</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_owner_contact_cell" VALUE="<?php echo $rrx_owner_contact_cell; ?>" disabled>
	
	<div class="field_title">Owner Contact Email</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_owner_contact_email" VALUE="<?php echo $rrx_owner_contact_email; ?>" disabled>

</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

<hr class="clear" />

<h1>Primary Contact Information</h1>

<p>The Primary ReconRx Contact will have access to the pharmacy's member's section and will receive fax, email and phone communications regarding missing and recovered payments.</p>

<div class="rrx-two-column-wrapper">

<div class="rrx-two-column">

   <div class="field_title">Primary Contact Name (Full)</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_main_contact_name" VALUE="<?php echo $rrx_main_contact_name; ?>" disabled>

   <div class="field_title">Primary Contact Title</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_main_contact_title" VALUE="<?php echo $rrx_main_contact_title; ?>" disabled>

   <div class="field_title">Primary Contact Email</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_main_contact_email" VALUE="<?php echo $rrx_main_contact_email; ?>" disabled>

</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

   <div class="field_title">Primary Contact Phone</div>
   <INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_main_contact_phone" VALUE="<?php echo $rrx_main_contact_phone; ?>" disabled>

   <div class="field_title">Primary Contact Cell</div>
   <INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_main_contact_cell" VALUE="<?php echo $rrx_main_contact_cell; ?>" disabled>

   <div class="field_title">Primary Contact Fax</div>
   <INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_main_contact_fax" VALUE="<?php echo $rrx_main_contact_fax; ?>" disabled>

</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

<hr class="clear" />

<h1>Signature Name for ReconRx Agreement</h1>

<p>Contract documents will be pre-populated with the name and title entered below for Authorized Signature.</p>

<div class="rrx-two-column-wrapper">

<div class="rrx-two-column">

   <div class="field_title">Authorized Signature Name (Full)</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_name" VALUE="<?php echo $rrx_auth_contact_name; ?>" disabled>

   <div class="field_title">Authorized Signature Title</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_title" VALUE="<?php echo $rrx_auth_contact_title; ?>" disabled>

   <div class="field_title">Authorized Signature Email</div>
   <INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_email" VALUE="<?php echo $rrx_auth_contact_email; ?>" disabled>

</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

   <div class="field_title">Authorized Signature Phone</div>
   <INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_auth_contact_phone" VALUE="<?php echo $rrx_auth_contact_phone; ?>" disabled>

   <div class="field_title">Authorized Signature Fax</div>
   <INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_auth_contact_fax" VALUE="<?php echo $rrx_auth_contact_fax; ?>" disabled>

</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

<hr class="clear" />

<h1>Payment Confirmation Contact</h1>

<p>The Payment Confirmation Contact will have access to the pharmacy member's section and will receive fax, email and phone communications regarding third party payments.</p>

<div class="rrx-two-column-wrapper">

<div class="rrx-two-column">

	<div class="field_title">Payment Confirmation Name (Full)</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_pmt_name" VALUE="<?php echo $rrx_auth_contact_pmt_name; ?>" disabled>

	<div class="field_title">Payment Confirmation Title</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_pmt_title" VALUE="<?php echo $rrx_auth_contact_pmt_title; ?>" disabled>
	
	<div class="field_title">Payment Confirmation Email</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_pmt_email" VALUE="<?php echo $rrx_auth_contact_pmt_email; ?>" disabled>

</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

	<div class="field_title">Payment Confirmation Phone</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_auth_contact_pmt_phone" VALUE="<?php echo $rrx_auth_contact_pmt_phone; ?>" disabled>

	<div class="field_title">Payment Confirmation Fax</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_auth_contact_pmt_fax" VALUE="<?php echo $rrx_auth_contact_pmt_fax; ?>" disabled>
	
</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

<hr class="clear" />

<h1>Claim Research Contact</h1>

<p>The Claim Research Contact will have access to the pharmacy member's section and will receive fax, email and phone communications regarding claim research.</p>

<div class="rrx-two-column-wrapper">

<div class="rrx-two-column">

	<div class="field_title">Claim Research Name (Full)</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_res_name" VALUE="<?php echo $rrx_auth_contact_res_name; ?>" disabled>

	<div class="field_title">Claim Research Title</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_res_title" VALUE="<?php echo $rrx_auth_contact_res_title; ?>" disabled>
	
	<div class="field_title">Claim Research Email</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_res_email" VALUE="<?php echo $rrx_auth_contact_res_email; ?>" disabled>

</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

	<div class="field_title">Claim Research Phone</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_auth_contact_res_phone" VALUE="<?php echo $rrx_auth_contact_res_phone; ?>" disabled>

	<div class="field_title">Claim Research Fax</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_auth_contact_res_fax" VALUE="<?php echo $rrx_auth_contact_res_fax; ?>" disabled>
	
</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

<hr class="clear" />

<h1>Additional Information</h1>

<div class="rrx-two-column-wrapper">

<div class="rrx-two-column">

      <div class="field_title">How did you hear about us?</div>
      <select name="rrx_how_did_you_hear_about_us" id="rrx_how_did_you_hear_about_us" class="rrx-input-text-form required" disabled>
      <?php 
      if ($rrx_how_did_you_hear_about_us == "") {
         echo "<option value=\"\" selected></option>";
      } else {
         echo "<option value=\"$rrx_how_did_you_hear_about_us\" selected>$rrx_how_did_you_hear_about_us</option>";
      } 
      ?>
      </select>

</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

      <div class="field_title">Promo Code*</div>
      <INPUT class="rrx-input-text-form" TYPE="text" NAME="rrx_promo_code" VALUE="<?php echo $rrx_promo_code; ?>" disabled>

      <p>* If you received a promo code please enter it here. It will be reviewed by our staff on completion of the enrollment.</p>

</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

</div><!-- end mainbody_front -->

<!-- Sidebar -------------------------------------------------------->
<div id="sidebarWrapper">
   <div id="sidebar">
   <h2>Details:</h2>
   <?php
   if ($admin_mode > 0) {
      $inDesktop = 0;
      $inRecon = 0;
      $sql = "
        SELECT a.Pharmacy_ID, a.NCPDP, a.Pharmacy_Name, a.Type, a.Status_ReconRx, a.Status_ReconRx_Clinic, a.Status_ReconRx_SP, b.COO_Date, a.Arete_Type
          FROM $db.$table a
          LEFT JOIN $db.pharmacy_coo b on a.ncpdp = b.ncpdp
         WHERE a.NCPDP = ?
      ";
      if ($pull = $mysqli->prepare("$sql")) {
         $pull->bind_param('i', $rrx_ncpdp);
         $pull->execute();
         $checkstore = $pull->get_result();
         while ($row = $checkstore->fetch_assoc()) {
            $pai_pharmacy_id = $row['Pharmacy_ID'];
            $pai_ncpdp       = $row['NCPDP'];
            $pai_name        = $row['Pharmacy_Name'];
            $pai_type        = $row['Type'];
            $status_rrx      = $row['Status_ReconRx'];
            $status_rrx_q    = $row['Status_ReconRx_Clinic'];
            $status_rrx_s    = $row['Status_ReconRx_SP'];
            $coo_date        = $row['COO_Date'];
            $service_level   = $row['Arete_Type'];
	    $inDesktop++;
	    if ($status_rrx != '' || $status_rrx_q != '' || $status_rrx_s != '') {
               $inRecon++;
	    }
            if (preg_match("/ReconRx/i", $pai_type)) {
               $inRecon++;
	    }
	    if($coo_date) {
              $disabled = 'disabled';
	    }

	    if($coo_date) {
	      $piece = explode("-", $coo_date);
              $coo_date = "$piece[1]/$piece[2]/$piece[0]";
	    }
         }
         $pull->close();
      }
      else {
	$dbproblem++;
        $myFile = "errors.txt";
        $fh = fopen($myFile, 'w') or die("can't open file5");
        fwrite($fh, $sql);
        fclose($fh);
      }
	  

      if ($inDesktop > 0 && !$COO) {
        if ($inRecon == 0)  {
    	  echo "<p><strong>Found in PAI Desktop! ID:$pai_pharmacy_id</strong></p>\n";
          echo "
          <p>
          <form action=\"\" method=\"post\">
          <input class=\"button-form\" TYPE=\"submit\" NAME=\"submit\" VALUE=\"Update Desktop\">
          <input type=\"hidden\" name=\"paidesktop\" value=\"true\">
          <input type=\"hidden\" name=\"admin_ncpdp\" value=\"$rrx_ncpdp\">
          <input type=\"hidden\" name=\"admin_npi\" value=\"$rrx_npi\">
         <input type=\"hidden\" name=\"admin_id\" value=\"$admin_id\">
          <input type=\"hidden\" name=\"admin_pharmacy_id\" value=\"$pai_pharmacy_id\">
         <input type=\"hidden\" id=\"arete_service_level\" name=\"arete_service_level\" value=\"$service_level\">
          </form>
          </p>\n";
	}
	else {
          echo "<p><strong>Already in ReconRx!</strong></p>\n";
          echo "<p>Name: $pai_name</p>\n";
          echo "<p>Type: $pai_type</p>\n";
	}
      }else if ($dbproblem) {
        echo "Connection Problems: Please contact your IT Dept\n";
      }else if ($COO && $coo_date> 0) {
          echo "<p><strong>Change of Ownership</strong></p>\n";
          echo "<p><strong>Already in ReconRx!</strong></p>\n";
          echo "<p>Name: $pai_name</p>\n";
          echo "<p>Type: $pai_type</p>\n";

      } else {
	    if ($COO) {
              echo "<p><strong>Change of Ownership</strong></p>\n";
            }
	    else {
              echo "<p><strong>Not yet in PAI Desktop.</strong></p>\n";
	    }
         ?>
         <form action="" name="form1" method="post"  onsubmit="return check_data()">
         <input class="button-form" TYPE="submit" NAME="submit" VALUE="Import to Desktop" >
         <?php
         echo "
         <p>
         <input type=\"hidden\" name=\"paidesktop\" value=\"true\">
         <input type=\"hidden\" name=\"admin_ncpdp\" value=\"$rrx_ncpdp\">
         <input type=\"hidden\" name=\"admin_npi\" value=\"$rrx_npi\">
         <input type=\"hidden\" id=\"new_ncpdp\" name=\"new_ncpdp\" value=\"$new_ncpdp\">
         <input type=\"hidden\" name=\"admin_id\" value=\"$admin_id\">
         <input type=\"hidden\" id=\"coo_date\" name=\"coo_date\" value=\"$coo_date\">
         <input type=\"hidden\" id=\"arete_service_level\" name=\"arete_service_level\" value=\"$service_level\">
         </form>
         </p>\n";
      }
	  
	  echo "
	  <p>
	  <form action=\"reconrx_enroll_complete.php\" method=\"post\">
	  <input class=\"button-form\" TYPE=\"submit\" VALUE=\"Regenerate Paperwork\">
	  <input type=\"hidden\" name=\"regenerate_ncpdp\" value=\"$rrx_ncpdp\">
	  <input type=\"hidden\" name=\"regenerate_npi\" value=\"$rrx_npi\">
         <input type=\"hidden\" name=\"admin_id\" value=\"$admin_id\">
         <input type=\"hidden\" id=\"coo_date\" name=\"coo_date\" value=\"$coo_date\">
         <input type=\"hidden\" id=\"arete_service_level\" name=\"arete_service_level\" value=\"$service_level\">
	  </form>
	  </p>\n";
	  
	  if ($rrx_status != 'archive') {
         echo "
         <p>
         <form action=\"\" method=\"post\">
         <input class=\"button-form\" TYPE=\"submit\" VALUE=\"Archive Enrollment\">
         <input type=\"hidden\" name=\"archive\" value=\"true\">
         <input type=\"hidden\" name=\"admin_ncpdp\" value=\"$rrx_ncpdp\">
         <input type=\"hidden\" name=\"admin_npi\" value=\"$rrx_npi\">
         <input type=\"hidden\" name=\"admin_id\" value=\"$admin_id\">
         </form>
         </p>\n";
	  } else {
		  echo "<p>Archived Enrollment</p>";
	  }
   }
   ?>
   </div> <!-- end sidebarWrapper -->
</div> <!-- end sidebar -->
<div id="sidebarWrapper">
<div id="sidebar2" style=<?php echo $display; ?>>
     <h2>Change of Ownership:</h2>
     <br>
     <div class="field_title">Contract Date</div>
	<div class="small_example">e.g. MM/DD/YYYY</div>
	<INPUT class="rrx-input-text-form datepicker required" TYPE="text" NAME="rrx_contract_date" ID="COO_Date" style="width:200px" VALUE="<?php echo $coo_date; ?>" maxlength="10" onchange="assign_coo_date(this.value)"<?php echo $disabled; ?>>
   </div> 
</div> <!-- end sidebarWrapper -->
<!------------------------------------------------------------------->
</formG
<!--Footer----------------------------------------------------------->
</div><!-- end content_container_front -->
<?php include 'includes/footer.php'; ?>
<!------------------------------------------------------------------->

</div>
<script>

function check_data() {
  var str = document.getElementById("COO_Date").value; 
  var a = (document.getElementById('sidebar2')).style;
  if (a.display != 'none' && str == "") { 
    alert('Invalid Contract Date');
    return false;
  }

  var str = document.getElementById("rrx_psao").value; 
  var ab = document.getElementById("rrx_service_levelB").checked; 
  var ae = document.getElementById("rrx_service_levelE").checked; 
  if(str == 'AlignRx' ) {
    if(!ab && !ae ) {
      alert("Please Select Service Type");
      return false;
    }
  }
}

function assign_coo_date(val) {
  var str = document.getElementById("COO_Date").value; 
  var array = str.split("/")
  var new_date = array[2]+"-"+array[0]+"-"+array[1];
  document.getElementById("coo_date").value  =  new_date;
}

function assign_service(val) {
  document.getElementById("arete_service_level").value  =  val;
}

$(function() {
	
	$(".datepicker").mask("99/99/9999");
	$( ".datepicker" ).datepicker();
	$( "#anim" ).change(function() {
	  $( ".datepicker" ).datepicker( "option", "showAnim", $( this ).val() );
	});
  
});
</script>

<?php
function add_contact($mysqli, $pharmacy_id, $contact_ctl_id, $name, $title, $email, $phone, $cell, $fax) {
  #  echo "INTO add_data<br>";
    
  if ($insert = $mysqli->prepare("
     REPLACE INTO officedb.pharmacy_contacts SET
        pharmacy_id = ?,
        contact_ctl_id = ?,
        name = ?,
        title = ?,
        email = ?,
        phone = ?,
        cellphone = ?,
        fax = ?
  ;")) {
     $insert->bind_param('iissssss',
     $pharmacy_id,
     $contact_ctl_id,	     
     $name,
     $title,
     $email,
     $phone,
     $cell,
     $fax
  );

    $insert->execute();

    echo $mysqli->error;

    $insert->close();
  }
  else {
    printf("Prepared Statement Error: %s\n", $mysqli->error);
    $myFile = "errors.txt";
    $fh = fopen($myFile, 'w') or die("can't open file1");
    fwrite($fh, $mysqli->error);
    fclose($fh);
  }
}


$mysqli->close();
?>

</body>
</html>
