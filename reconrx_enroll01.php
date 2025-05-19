<?php

include 'includes/mysql.php';

$rrx_page = basename($_SERVER['PHP_SELF']);
$curdate = date("Y-m-d");
$errorcheck = 0;
$usercheck = -1;
$row_cnt = 0;

$rrx_enrollment_start = $curdate;

if (isset($_GET['source'])) { $source = $_GET['source']; } else { $source = ""; }
if (isset($_GET['caller'])) { $caller = $_GET['caller']; } else { $caller = ""; }
if (isset($_GET['promo']))  { $promo  = $_GET['promo']; }  else { $promo  = ""; }

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

###USER CHECK FOR DUPS#############################################

if (($rrx_ncpdp != "")) {
	if ($stmt = $mysqli->prepare("
		SELECT pharmacy_id, COO FROM reconrxdb.enrollment a
                LEFT JOIN officedb.pharmacy b  on b.NCPDP = a.rrx_ncpdp 
                 WHERE a.rrx_ncpdp= ?
                 ORDER BY COO DESC
		;")) {
		$stmt->bind_param('i', $rrx_ncpdp);
		$stmt->execute();
		$stmt->store_result();
	        $stmt->bind_result($coo_id, $old_coo);
                $stmt->fetch(); 
		$row_cnt = $stmt->num_rows;
		$stmt->close();

		if ($row_cnt > 0) {
			$usercheck = 0;
			if(($coo) && ($old_coo != $coo_id)) {
			    $usercheck = 1;
			}
		} else {
			$usercheck = 1;
		}
	}
	else {
		printf("Prepared Statement Error: %s\n", $mysqli->error);
		$errorcheck = 2;
	}

	if ($usercheck == 1) {
		if ( $login_or == 'Y' ) {
			if ($stmt = $mysqli->prepare("
        	                SELECT id
                	          FROM officedb.weblogin
                        	 WHERE login = '$rrx_login'
				   AND password = AES_ENCRYPT('$rrx_password','PAI20181217!')
        	                 UNION 
				SELECT id
                		  FROM reconrxdb.enrollment
		                 WHERE rrx_login= '$rrx_login'
				   AND rrx_password = '$rrx_password'
				;")) {
				$stmt->execute();
				$stmt->store_result();
			        $stmt->bind_result($login_id);
        	        	$stmt->fetch(); 
				$row_cnt = $stmt->num_rows;
				$stmt->close();
		
				if ($row_cnt > 0) {
					$usercheck = 1;
				} else {
					$usercheck = 4;
				}
			}
			else {
				printf("Prepared Statement Error: %s\n", $mysqli->error);
				$errorcheck = 2;
			}
		}
		else {
			if ($stmt = $mysqli->prepare("
        	                SELECT id
                	          FROM officedb.weblogin
                        	 WHERE login = '$rrx_login'
        	                 UNION 
				SELECT id
                		  FROM reconrxdb.enrollment
		                 WHERE rrx_login= '$rrx_login'
				;")) {
				$stmt->execute();
				$stmt->store_result();
			        $stmt->bind_result($login_id);
        	        	$stmt->fetch(); 
				$row_cnt = $stmt->num_rows;
				$stmt->close();
		
				if ($row_cnt > 0) {
					$usercheck = 3;
				} else {
					$usercheck = 1;
				}
			}
			else {
				printf("Prepared Statement Error: %s\n", $mysqli->error);
				$errorcheck = 2;
			}
		}
	}
	
}

if(!$coo_id) {
  $coo_id = '0';
}

if ($usercheck == 1) {
	if ($rrx_ncpdp != "") {
	
		$rrx_status = "pending";
                if ($coo) {
		  $rrx_status = "pending_coo";
                }
		
		if ($rrx_eoy != "") {
			$pcs = explode('/', $rrx_eoy);
			$rrx_eoy = $pcs[2] . "-" . $pcs[0] . "-" . $pcs[1];
		} else {
			$rrx_eoy = NULL;
		}
		
		if ($rrx_swvendor_other != "") {
			$rrx_swvendor = $rrx_swvendor_other;
		}

                if($promo) {
		    $rrx_promo_code = "$promo";
		}

                if($caller) {
                  if($caller == 'GR') {
		    $rrx_affiliate = 'Guaranteed Returns';
		  }
		  elseif ($caller == 'Ontime') {
		    $rrx_affiliate = 'Ontime Soft';
		  }
		  else {
                    $rrx_affiliate = $caller;
		  }

                  $rrx_how_did_you_hear_about_us = "$rrx_affiliate";
	        }

		if ($stmt = $mysqli->prepare("
			INSERT INTO reconrxdb.enrollment SET 
			rrx_status = ?, 
			rrx_enrollment_start = ?, 
			rrx_pharmname = ?, 
			rrx_legalname = ?, 
			rrx_comm_pref = ?,
			rrx_phone = ?, 
			rrx_ncpdp = ?, 
			rrx_npi = ?, 
			rrx_fax = ?, 
			rrx_email = ?, 
			rrx_main_address1 = ?, 
			rrx_main_address2 = ?, 
			rrx_main_city = ?, 
			rrx_main_state = ?, 
			rrx_main_zip = ?, 
			rrx_main_county_parish = ?, 
			rrx_mailing_address1 = ?, 
			rrx_mailing_address2 = ?, 
			rrx_mailing_city = ?, 
			rrx_mailing_state = ?, 
			rrx_mailing_zip = ?, 
			rrx_mailing_county_parish = ?, 
			rrx_fed_tax_class = ?, 
			rrx_fed_tax_id = ?, 
			rrx_state_tax_id = ?, 
			rrx_medicaid = ?, 
			rrx_swvendor = ?, 
			rrx_switch = ?, 
			rrx_switch_secondary = ?, 
			rrx_wholesaler = ?, 
			rrx_psao = ?, 
			rrx_eoy = ?, 
			rrx_owner_contact_name = ?, 
			rrx_owner_contact_phone = ?, 
			rrx_owner_contact_fax = ?, 
			rrx_owner_contact_cell = ?, 
			rrx_owner_contact_email = ?, 
			rrx_main_contact_name = ?, 
			rrx_main_contact_title = ?, 
			rrx_main_contact_email = ?, 
			rrx_main_contact_cell = ?, 
			rrx_main_contact_phone = ?, 
			rrx_main_contact_ext = ?, 
			rrx_main_contact_fax = ?, 
			rrx_auth_contact_name = ?, 
			rrx_auth_contact_title = ?, 
			rrx_auth_contact_email = ?, 
			rrx_auth_contact_phone = ?, 
			rrx_auth_contact_fax = ?,
			rrx_auth_contact_pmt_name = ?,
			rrx_auth_contact_pmt_title = ?, 
			rrx_auth_contact_pmt_email = ?, 
			rrx_auth_contact_pmt_phone = ?, 
			rrx_auth_contact_pmt_fax = ?, 
			rrx_auth_contact_res_name = ?, 
			rrx_auth_contact_res_title = ?, 
			rrx_auth_contact_res_email = ?, 
			rrx_auth_contact_res_phone = ?, 
			rrx_auth_contact_res_fax = ?, 
			rrx_source = ?, 
			rrx_how_did_you_hear_about_us = ?,
			rrx_promo_code = ?,
			rrx_hours_monday=?, 
			rrx_hours_tuesday=?, 
			rrx_hours_wednesday=?, 
			rrx_hours_thursday=?, 
			rrx_hours_friday=?, 
			rrx_hours_saturday=?, 
			rrx_hours_sunday=?,
			rrx_service_level=?,
			rrx_login=?,
			rrx_password=?,
                        rrx_affiliate=?,
			COO = ?
			;")) {
			$stmt->bind_param('ssssssiissssssisssssissssssssssssssssssssssssssssssssssssssssssssssssssssi', $rrx_status, $rrx_enrollment_start, $rrx_pharmname, $rrx_legalname, $rrx_comm_pref, $rrx_phone, $rrx_ncpdp, $rrx_npi, $rrx_fax, $rrx_email, $rrx_main_address1, $rrx_main_address2, $rrx_main_city, $rrx_main_state, $rrx_main_zip, $rrx_main_county_parish, $rrx_mailing_address1, $rrx_mailing_address2, $rrx_mailing_city, $rrx_mailing_state, $rrx_mailing_zip, $rrx_mailing_county_parish, $rrx_fed_tax_class, $rrx_fed_tax_id, $rrx_state_tax_id, $rrx_medicaid, $rrx_swvendor, $rrx_switch, $rrx_switch_secondary, $rrx_wholesaler, $rrx_psao, $rrx_eoy, $rrx_owner_contact_name, $rrx_owner_contact_phone, $rrx_owner_contact_fax, $rrx_owner_contact_cell, $rrx_owner_contact_email, $rrx_main_contact_name, $rrx_main_contact_title, $rrx_main_contact_email, $rrx_main_contact_cell, $rrx_main_contact_phone, $rrx_main_contact_ext, $rrx_main_contact_fax, $rrx_auth_contact_name, $rrx_auth_contact_title, $rrx_auth_contact_email, $rrx_auth_contact_phone, $rrx_auth_contact_fax, $rrx_auth_contact_pmt_name, $rrx_auth_contact_pmt_title, $rrx_auth_contact_pmt_email, $rrx_auth_contact_pmt_phone, $rrx_auth_contact_pmt_fax, $rrx_auth_contact_res_name, $rrx_auth_contact_res_title, $rrx_auth_contact_res_email, $rrx_auth_contact_res_phone, $rrx_auth_contact_res_fax, $source, $rrx_how_did_you_hear_about_us, $rrx_promo_code, $rrx_hours_monday, $rrx_hours_tuesday, $rrx_hours_wednesday, $rrx_hours_thursday, $rrx_hours_friday, $rrx_hours_saturday, $rrx_hours_sunday, $rrx_service_level, $rrx_login, $rrx_password,$rrx_affiliate, $coo_id);
                        if (!$stmt->execute()) {
                          $errmsg = "Execute Statement Error: $stmt->error";
                          $errorcheck = 1;
                        }
			printf("Prepared Statement Error: %s\n", $stmt->error);
			$stmt->close();
		}
		else {
			printf("Prepared Statement Error: %s\n", $mysqli->error);
			$errmsg = "Prepared Statement Error: $mysqli->error";
			$errorcheck = 1;
		}
		
		if ($errorcheck != 1 && ($usercheck == 1 || $coo)) {
			setcookie("rrx_ncpdp", "$rrx_ncpdp", time()+43200);
			setcookie("rrx_npi", "$rrx_npi", time()+43200);
				header('Location: reconrx_enroll_complete.php');
			exit();
		}
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

<script>
$(function() {
	
	$(".datepicker").mask("99/99/9999");
	$('.phone').mask('(999) 999-9999');
	$(".ncpdp").mask("9999999",{placeholder:" "});
	$(".npi").mask("9999999999",{placeholder:" "});
	$('.zip').mask("99999",{placeholder:" "});
	
	$( ".datepicker" ).datepicker();
	$( "#anim" ).change(function() {
		$( ".datepicker" ).datepicker( "option", "showAnim", $( this ).val() );
	});
  
	$('#swvendor').change(function() {
		$("#otherType")[$(this).val() == "Other" ? 'show' : 'hide']("fast");
	}).change();
	
	$("#same_address").on("change", function(){
		if (this.checked) {
			$("[name='rrx_mailing_address1']")     .val($("[name='rrx_main_address1']").val());
			$("[name='rrx_mailing_address2']")     .val($("[name='rrx_main_address2']").val());
			$("[name='rrx_mailing_city']")         .val($("[name='rrx_main_city']").val());
			$("[name='rrx_mailing_state']")        .val($("[name='rrx_main_state']").val());
			$("[name='rrx_mailing_zip']")          .val($("[name='rrx_main_zip']").val());
			$("[name='rrx_mailing_county_parish']").val($("[name='rrx_main_county_parish']").val());
		}
	});

	$("#same_contact").on("change", function(){
		if (this.checked) {
			$("[name='rrx_main_contact_name']")     .val($("[name='rrx_owner_contact_name']").val());
			$("[name='rrx_main_contact_email']")    .val($("[name='rrx_owner_contact_email']").val());
			$("[name='rrx_main_contact_phone']")    .val($("[name='rrx_owner_contact_phone']").val());
			$("[name='rrx_main_contact_cell']")     .val($("[name='rrx_owner_contact_cell']").val());
			$("[name='rrx_main_contact_fax']")      .val($("[name='rrx_owner_contact_fax']").val());
			$("[name='rrx_main_contact_title']")    .val('Owner');
		}
	});
	$("#same_contact_authorized").on("change", function(){
		if (this.checked) {
			$("[name='rrx_auth_contact_name']")     .val($("[name='rrx_owner_contact_name']").val());
			$("[name='rrx_auth_contact_email']")    .val($("[name='rrx_owner_contact_email']").val());
			$("[name='rrx_auth_contact_phone']")    .val($("[name='rrx_owner_contact_phone']").val());
			$("[name='rrx_auth_contact_fax']")      .val($("[name='rrx_owner_contact_fax']").val());
			$("[name='rrx_auth_contact_title']")    .val('Owner');
		}
	});
	$("#same_contact_pmt").on("change", function(){
		if (this.checked) {
			$("[name='rrx_auth_contact_pmt_name']")     .val($("[name='rrx_owner_contact_name']").val());
			$("[name='rrx_auth_contact_pmt_email']")    .val($("[name='rrx_owner_contact_email']").val());
			$("[name='rrx_auth_contact_pmt_phone']")    .val($("[name='rrx_owner_contact_phone']").val());
			$("[name='rrx_auth_contact_pmt_fax']")      .val($("[name='rrx_owner_contact_fax']").val());
			$("[name='rrx_auth_contact_pmt_title']")    .val('Owner');
		}
	});
	$("#same_contact_res").on("change", function(){
		if (this.checked) {
			$("[name='rrx_auth_contact_res_name']")     .val($("[name='rrx_owner_contact_name']").val());
			$("[name='rrx_auth_contact_res_email']")    .val($("[name='rrx_owner_contact_email']").val());
			$("[name='rrx_auth_contact_res_phone']")    .val($("[name='rrx_owner_contact_phone']").val());
			$("[name='rrx_auth_contact_res_fax']")      .val($("[name='rrx_owner_contact_fax']").val());
			$("[name='rrx_auth_contact_res_title']")    .val('Owner');
		}
	});

	$("#rrx_psao").on("change", function(){
		if ($('#rrx_psao').val() == 'AlignRx' ) {
			$('#svc_level').show();
        			document.getElementById("rrx_service_level").classList.add('required');
        		} else {
        			$('#svc_level').hide();
        		}
	});
});
</script>
<script src="/includes/checkRequiredFields.js"></script>

<?php
  if ($caller) {
    $urlparam = "?caller=$caller";
  }
  if ($promo) {
    $urlparam = "?promo=$promo";
  }
?>

<h1>Let's get started!</h1>
<form name="enroll" id="enroll" action="reconrx_enroll01.php<?php echo $urlparam; ?>" onsubmit="return checkRequiredFields(this)" method="post">
<!-- return validateForm() -->
<?php
if ($usercheck == 0) {
	echo "<span class=\"notice\">We're sorry, it appears that this pharmacy (NCPDP: $rrx_ncpdp) has already submitted an enrollment. <a href=\"continue_enrollment.php\">Click here</a> to re-download a completed enrollment. Please call (888) 255-6526 for help.</span>";
}	
if ($usercheck == 3) {
	echo "<span class=\"notice\">We're sorry, but this login has already been used.  If you are aware of this and enrolling in additional programs or pharmacies into this program, acknowledge this by clicking the box below and re-submitting your enrollment. Otherwise, please use another login. Please call (888) 255-6526 for help.</span><br><strong>Existing login over-ride</strong> <INPUT TYPE='checkbox' NAME='login_or' VALUE='Y'>";
}

if ($usercheck == 4) {
	echo "<span class=\"notice\">We're sorry, but the password provided did not match this login.  Please use a different login or call (888) 255-6526 for help.</span>";
}
#if ($errorcheck == 1) {
#	echo "<span class=\"notice\">We're sorry, $errmsg</span>";
#}
?>

<div class="rrx-two-column-wrapper clear">

<p>Please complete the following sections. Once completed and submitted, you will be sent pre-populated documents to sign through DocuSign.</p>

<?php
$entity = 'Pharmacy';
$entity_lc = "pharmacy's";
?>

</div> <!-- end rrx-two-column-wrapper -->


<hr class="clear" />


<div class="rrx-two-column-wrapper">

<div class="rrx-two-column">
<div class="field_title"> </div>
  <h1><?php echo $entity; ?> Information</h1>

  <div class="field_title"> </div>
  <div class="field_title">NCPDP</div>
  <INPUT class="rrx-input-text-form required " id="NCPDP" TYPE="text" NAME="rrx_ncpdp" placeholder="Please enter NCPDP first" VALUE="<?php echo $rrx_ncpdp; ?>" maxlength="7" onkeyup="checkNCPDP(this.value, <?php echo "'$caller'"; ?>,<?php echo "'$promo'"; ?>, )">

	<div class="field_title"><?php echo $entity; ?> Name</div>
	<INPUT class="rrx-input-text-form required" id='PharmName' TYPE="text" NAME="rrx_pharmname" VALUE="<?php echo $rrx_pharmname; ?>" maxlength="255">

	<div class="field_title"><?php echo $entity; ?> Legal Name</div>
	<INPUT class="rrx-input-text-form required Legal Name" TYPE="text" ID="Legal_Name" NAME="rrx_legalname" VALUE="<?php echo $rrx_legalname; ?>" maxlength="255">

	<div class="field_title">Federal Tax Class</div>
	<select name="rrx_fed_tax_class" class="rrx-dropdown-form required" id="FedTaxClass">
	<option value="<?php echo $rrx_fed_tax_class; ?>" selected><?php echo $rrx_fed_tax_class; ?></option>
	<option value="C-Corp">C-Corp</option>
	<option value="LLC">LLC</option>
	<option value="Non Profit/Exempt">Non Profit/Exempt</option>
	<option value="Partnership">Partnership</option>
	<option value="S-Corp">S-Corp</option>
	<option value="Sole Proprietor">Sole Proprietor</option>
	</select>
	
	<div class="field_title">Medicaid Number</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_medicaid" ID="MedNumber" VALUE="<?php echo $rrx_medicaid; ?>" maxlength="20">
	
	<div class="field_title">Software Vendor</div>
	<select name="rrx_swvendor" id="SWVendor" class="rrx-dropdown-form swvendor required">
	<?php 
	if ($rrx_swvendor == "") {
		echo "<option value=\"\" selected></option>";
	} else {
		echo "<option value=\"$rrx_swvendor\" selected>$rrx_swvendor</option>";
	} 
	
	$sql = "
	SELECT Vals FROM officedb.opts 
	WHERE OPTS_ID = 1100 #Software Vendors
	";
	if ($pull = $mysqli->query("$sql")) {
		while ($row = $pull->fetch_assoc()) {
			$SW_Vendors_String = $row['Vals'];
		}
		$SW_Vendors_Array = explode(", ", $SW_Vendors_String);
		sort($SW_Vendors_Array);
		foreach ($SW_Vendors_Array as $vendor) {
                  if($caller == 'Ontime') {
		    if($vendor != 'Rx30') {continue;}
		    $selected = "selected='selected'";
	       	  }
		  echo "<option $selected value=\"$vendor\">$vendor</option>";
		}
	}
        if($caller != 'Ontime') {
	  echo "<option value=\"Other\">Other</option>";
	}
	
	?>

	</select>
	
	<div id="otherType" style="display:none;">
	<div class="field_title">Other Software Vendor</div>
	<INPUT TYPE="text" NAME="rrx_swvendor_other" class="rrx-input-text-form swvendor_other" VALUE="<?php echo $rrx_swvendor_other; ?>" maxlength="100">
	</div>
	
	<div class="field_title">Drug Wholesaler</div>
	<select name="rrx_wholesaler" class="rrx-dropdown-form swvendor required">
	<?php 
	if ($rrx_wholesaler == "") {
		echo "<option value=\"\" selected></option>";
	} else {
		echo "<option value=\"$rrx_wholesaler\" selected>$rrx_wholesaler</option>";
	} 
	
	$sql = "
	SELECT Vals FROM officedb.opts 
	WHERE OPTS_ID = 1600 #Drug Wholesalers
	";
	if ($pull = $mysqli->query("$sql")) {
		while ($row = $pull->fetch_assoc()) {
			$Wholesalers_String = $row['Vals'];
		}
		$Wholesalers_Array = explode(", ", $Wholesalers_String);
		sort($Wholesalers_Array);
		foreach ($Wholesalers_Array as $vendor) {
			if (preg_match("/N\/A/i", $vendor)) { continue; }
			if (preg_match("/other/i", $vendor)) { continue; }
			echo "<option value=\"$vendor\">$vendor</option>";
		}
	}
	echo "<option value=\"Other\">Other</option>";
	
	?>
	</select>
	
	<div class="field_title">End of your current Fiscal Year</div>
	<div class="small_example">e.g. MM/DD/YYYY</div>
	<INPUT class="rrx-input-text-form datepicker required" TYPE="text" NAME="rrx_eoy" ID="EOY" VALUE="<?php echo $rrx_eoy; ?>" maxlength="10">

	
</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

	<div class="field_title" style="padding-bottom: 41px "> </div>

	<div class="field_title">NPI</div>
	<INPUT class="rrx-input-text-form required npi" ID="NPI" TYPE="text" NAME="rrx_npi" VALUE="<?php echo $rrx_npi; ?>" maxlength="10">
	
	<div class="field_title">Federal Tax ID</div>
	<INPUT class="rrx-input-text-form required" id="FedTaxID" TYPE="text" NAME="rrx_fed_tax_id" VALUE="<?php echo $rrx_fed_tax_id; ?>" maxlength="10">
	
	<div class="field_title">Switch Company (Primary)</div>
	<select name="rrx_switch" id="PrimSwitch" class="rrx-dropdown-form swvendor required">
	<?php 
	if ($rrx_switch == "") {
		echo "<option value=\"\" selected></option>";
	} else {
		echo "<option value=\"$rrx_switch\" selected>$rrx_switch</option>";
	} 

	$sql = "
	SELECT Vals FROM officedb.opts 
	WHERE OPTS_ID = 1110 #Switch Vendors
	";
	if ($pull = $mysqli->query("$sql")) {
		while ($row = $pull->fetch_assoc()) {
			$Switch_Vendors_String = $row['Vals'];
		}
		$Switch_Vendors_Array = explode(", ", $Switch_Vendors_String);
		sort($Switch_Vendors_Array);
		foreach ($Switch_Vendors_Array as $vendor) {
			if (preg_match("/N\/A/", $vendor)) { continue; }
			echo "<option value=\"$vendor\">$vendor</option>";
		}
	}
	echo "<option value=\"Other\">Other</option>";
	
	?>
	</select>
	
	<div class="field_title">Switch Company (Secondary)</div>
	<select name="rrx_switch_secondary" id="SecSwitch"  class="rrx-dropdown-form swvendor required">
	<?php 
	if ($rrx_switch_secondary == "") {
		echo "<option value=\"\" selected></option>";
	} else {
		echo "<option value=\"$rrx_switch_secondary\" selected>$rrx_switch_secondary</option>";
	} 
	echo "<option value=\"N/A\">N/A</option>";
	foreach ($Switch_Vendors_Array as $vendor) {
		if (preg_match("/N\/A/", $vendor)) { continue; }
		echo "<option value=\"$vendor\">$vendor</option>";
	}
	echo "<option value=\"Other\">Other</option>";
	?>
	</select>
	
	<div class="field_title">Current PSAO</div>
	<select name="rrx_psao" id="rrx_psao" class="rrx-dropdown-form swvendor required">
	<?php 
	if ($rrx_psao == "") {
		echo "<option value=\"\" selected></option>";
	} else {
		echo "<option value=\"$rrx_psao\" selected>$rrx_psao</option>";
	} 
        $vendor_exc = '2000061'; ##Jessie request 20221026
	$sql = "
	SELECT Vendor_ID, Vendor_Name
          FROM officedb.vendor
	 WHERE Type = 'PSAO'
	   AND Status = 'Active'
           && Vendor_ID NOT IN ($vendor_exc)
      ORDER BY Vendor_Name
        ";

	if ($pull = $mysqli->query("$sql")) {
	  while ($row = $pull->fetch_assoc()) {
	     $selected = '';
	     $vendor_id = $row['Vendor_Name'];
	     $vendor_name = $row['Vendor_Name'];
	     if($caller == 'GeriMed' && $vendor_name == 'GeriMed') {
               $selected = "selected='selected'";
	     }
             echo "<option $selected value=\"$vendor_id\">$vendor_name</option>";
	  }
	}

	echo "<option value=\"No PSAO\">No PSAO</option>";

	?>
	</select>

	<div id="svc_level" style="display: none;">
	<input type="radio" name="rrx_service_level" id="rrx_service_level" value="B" <?php if ($pull_service_level == 'B') { echo 'checked'; } ?> class="Basic"> Basic
	<input type="radio" name="rrx_service_level" value="E" <?php if ($pull_service_level == 'E') { echo 'checked'; } ?>> Enhanced Plus
        </div>
	
</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

<input type="hidden" id="coo" name="coo" VALUE="<?php echo $coo; ?>">

<hr class="clear" /><br />

<div class="rrx-two-column-wrapper">
<div class="rrx-two-column">

	<div class="field_title">Phone (<?php echo $entity; ?>)</div>
	<div class="small_example">e.g. (555) 555-5555</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" ID="Phone" NAME="rrx_phone" VALUE="<?php echo $rrx_phone; ?>" maxlength="255">

	<div class="field_title">Fax (<?php echo $entity; ?>)</div>
	<div class="small_example">e.g. (555) 555-5555</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_fax" ID="Fax"  VALUE="<?php echo $rrx_fax; ?>" maxlength="15">
	
</div> <!-- rrx-two-column -->
<div class="rrx-two-column">

	<div class="field_title">Email (<?php echo $entity; ?>)</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_email" ID="Email" VALUE="<?php echo $rrx_email; ?>" maxlength="64">
	
	<div class="field_title">Communication Preference</div>
	<select name="rrx_comm_pref" id="CommPref" class="rrx-dropdown-form required">
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
		<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_login" VALUE="<?php echo $rrx_login; ?>" maxlength="100">
	
</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

		<div class="field_title">Password</div>
		<INPUT class="rrx-input-text-form required" TYPE="password" NAME="rrx_password" VALUE="<?php echo $rrx_password; ?>" maxlength="32">
		

</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

		<p>* These will be the credentials used to login to our website once your agreement has been processed and pharmacy made active.</p>

<hr class="clear" />

<h1><?php echo $entity; ?> Address</h1>

<div class="rrx-two-column-wrapper">

<div class="rrx-two-column">
	
	<h2>Physical Address</h2>

	<div class="field_title">Address Line 1</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" ID="Address" NAME="rrx_main_address1" VALUE="<?php echo $rrx_main_address1; ?>" maxlength="255">

	<div class="field_title">Address Line 2</div>
	<INPUT class="rrx-input-text-form" TYPE="text" NAME="rrx_main_address2" VALUE="<?php echo $rrx_main_address2; ?>" maxlength="255">

	<div class="field_title">City</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" ID="City" NAME="rrx_main_city" VALUE="<?php echo $rrx_main_city; ?>" maxlength="255">
	
	<div class="field_title">State</div>
	<select name="rrx_main_state" id="State" class="rrx-dropdown-form required">
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
	<option value="PR">PR</option>
	<option value="RI">RI</option>
	<option value="SC">SC</option>
	<option value="SD">SD</option>
	<option value="TN">TN</option>
	<option value="TX">TX</option>
	<option value="UT">UT</option>
	<option value="VT">VT</option>
	<option value="VA">VA</option>
	<option value="VI">VI</option>
	<option value="WA">WA</option>
	<option value="WV">WV</option>
	<option value="WI">WI</option>
	<option value="WY">WY</option>
	</select>
	
	<div class="field_title">Zip</div>
	<INPUT class="rrx-input-text-form required zip" TYPE="text" NAME="rrx_main_zip" ID="Zip" VALUE="<?php echo $rrx_main_zip; ?>" maxlength="5">
	
	<div class="field_title">County or Parish</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_main_county_parish" VALUE="<?php echo $rrx_main_county_parish; ?>" maxlength="255">
	
</div> <!-- rrx-two-column -->

<div class="rrx-two-column">
	
	<h2>Mailing Address
	<input type="checkbox" id="same_address" name="same_address"><p style="display: inline;">Same as physical</p>
	</h2>
	

	<div class="field_title">Address Line 1</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_mailing_address1" ID="Mail_Address" VALUE="<?php echo $rrx_mailing_address1; ?>" maxlength="255">

	<div class="field_title">Address Line 2</div>
	<INPUT class="rrx-input-text-form" TYPE="text" NAME="rrx_mailing_address2" VALUE="<?php echo $rrx_mailing_address2; ?>" maxlength="255">

	<div class="field_title">City</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_mailing_city" ID="Mail_City" VALUE="<?php echo $rrx_mailing_city; ?>" maxlength="255">
	
	<div class="field_title">State</div>
	<select name="rrx_mailing_state" id="Mail_State" class="rrx-dropdown-form required">
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
	<option value="PR">PR</option>
	<option value="RI">RI</option>
	<option value="SC">SC</option>
	<option value="SD">SD</option>
	<option value="TN">TN</option>
	<option value="TX">TX</option>
	<option value="UT">UT</option>
	<option value="VT">VT</option>
	<option value="VA">VA</option>
	<option value="VI">VI</option>
	<option value="WA">WA</option>
	<option value="WV">WV</option>
	<option value="WI">WI</option>
	<option value="WY">WY</option>
	</select>
	
	<div class="field_title">Zip</div>
	<INPUT class="rrx-input-text-form required zip" TYPE="text" NAME="rrx_mailing_zip" ID="Mail_Zip" VALUE="<?php echo $rrx_mailing_zip; ?>" maxlength="5">
	
	<div class="field_title">County or Parish</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_mailing_county_parish" VALUE="<?php echo $rrx_mailing_county_parish; ?>" maxlength="255">
	
</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

<hr class="clear" />

<h1>Pharmacy Days of Operation</h1>

<p>Please indicate if your pharmacy is open or close each day of the week.</p>

<div class="field_title">Monday</div>
<select name="rrx_hours_monday" id="rrx_hours_monday" class="rrx-dropdown-form required">
<option value="" <?php if ($rrx_hours_monday == "") {echo "selected";} ?> ></option>
<option value="open" <?php if (($rrx_hours_monday != "") && ($rrx_hours_monday != "closed")) {echo "selected";} ?> >open</option>
<option value="closed" <?php if ($rrx_hours_monday == "closed") {echo "selected";} ?> >closed</option>
</select>

<div class="field_title">Tuesday</div>
<select name="rrx_hours_tuesday" id="rrx_hours_tuesday" class="rrx-dropdown-form required">
<option value="" <?php if ($rrx_hours_tuesday == "") {echo "selected";} ?> ></option>
<option value="open" <?php if (($rrx_hours_tuesday != "") && ($rrx_hours_tuesday != "closed")) {echo "selected";} ?> >open</option>
<option value="closed" <?php if ($rrx_hours_tuesday == "closed") {echo "selected";} ?> >closed</option>
</select>

<div class="field_title">Wednesday</div>
<select name="rrx_hours_wednesday" id="rrx_hours_wednesday" class="rrx-dropdown-form required">
<option value="" <?php if ($rrx_hours_wednesday == "") {echo "selected";} ?> ></option>
<option value="open" <?php if (($rrx_hours_wednesday != "") && ($rrx_hours_wednesday != "closed")) {echo "selected";} ?> >open</option>
<option value="closed" <?php if ($rrx_hours_wednesday == "closed") {echo "selected";} ?> >closed</option>
</select>

<div class="field_title">Thursday</div>
<select name="rrx_hours_thursday" id="rrx_hours_thursday" class="rrx-dropdown-form required">
<option value="" <?php if ($rrx_hours_thursday == "") {echo "selected";} ?> ></option>
<option value="open" <?php if (($rrx_hours_thursday != "") && ($rrx_hours_thursday != "closed")) {echo "selected";} ?> >open</option>
<option value="closed" <?php if ($rrx_hours_thursday == "closed") {echo "selected";} ?> >closed</option>
</select>

<div class="field_title">Friday</div>
<select name="rrx_hours_friday" id="rrx_hours_friday" class="rrx-dropdown-form required">
<option value="" <?php if ($rrx_hours_friday == "") {echo "selected";} ?> ></option>
<option value="open" <?php if (($rrx_hours_friday != "") && ($rrx_hours_friday != "closed")) {echo "selected";} ?> >open</option>
<option value="closed" <?php if ($rrx_hours_friday == "closed") {echo "selected";} ?> >closed</option>
</select>

<div class="field_title">Saturday</div>
<select name="rrx_hours_saturday" id="rrx_hours_saturday" class="rrx-dropdown-form required">
<option value="" <?php if ($rrx_hours_saturday == "") {echo "selected";} ?> ></option>
<option value="open" <?php if (($rrx_hours_saturday != "") && ($rrx_hours_saturday != "closed")) {echo "selected";} ?> >open</option>
<option value="closed" <?php if ($rrx_hours_saturday == "closed") {echo "selected";} ?> >closed</option>
</select>

<div class="field_title">Sunday</div>
<select name="rrx_hours_sunday" id="rrx_hours_sunday" class="rrx-dropdown-form required">
<option value="" <?php if ($rrx_hours_sunday == "") {echo "selected";} ?> ></option>
<option value="open" <?php if (($rrx_hours_sunday != "") && ($rrx_hours_sunday != "closed")) {echo "selected";} ?> >open</option>
<option value="closed" <?php if ($rrx_hours_sunday == "closed") {echo "selected";} ?> >closed</option>
</select>

<hr class="clear" />

<h1>Owner Contact Information</h1>

<div class="rrx-two-column-wrapper">

<div class="rrx-two-column">

	<div class="field_title">Owner Name (Full)</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_owner_contact_name" ID="OwnerName" VALUE="<?php echo $rrx_owner_contact_name; ?>" maxlength="100">
	
	<div class="field_title">Owner Contact Email</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_owner_contact_email" ID="OwnerEmail"  VALUE="<?php echo $rrx_owner_contact_email; ?>" maxlength="128">

</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

	<div class="field_title">Owner Contact Phone</div>
	<div class="small_example">e.g. (555) 555-5555</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_owner_contact_phone" ID="OwnerPhone" VALUE="<?php echo $rrx_owner_contact_phone; ?>" maxlength="30">
	<div class="field_title">Owner Contact Cell</div>
	<div class="small_example">e.g. (555) 555-5555</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_owner_contact_cell" ID="OwnerCell" VALUE="<?php echo $rrx_owner_contact_cell; ?>" maxlength="30">

	<div class="field_title">Owner Contact Fax</div>
	<div class="small_example">e.g. (555) 555-5555</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_owner_contact_fax" ID="OwnerFax" VALUE="<?php echo $rrx_owner_contact_fax; ?>" maxlength="30">
	

</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->
<hr class="clear" />

<div class="rrx-two-column-wrapper">
<table class="noborder">
<tr><td><h1>Primary Contact Information</h1></td>
<td><input type="checkbox" id="same_contact" name="same_contact"><p style="display: inline;">Same as Owner Contact Information</p></td>
</tr>

<tr>
<td colspan='2'><p>The Primary ReconRx Contact will have access to the <?php echo $entity_lc; ?> member's section and will receive fax, email and phone communications regarding missing and recovered payments.</p</td>
</tr>
</table>

<div class="rrx-two-column">
	<div class="field_title">Primary Contact Name (Full)</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_main_contact_name" VALUE="<?php echo $rrx_main_contact_name; ?>" maxlength="100">

	<div class="field_title">Primary Contact Title</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_main_contact_title" VALUE="<?php echo $rrx_main_contact_title; ?>" maxlength="100">
	
	<div class="field_title">Primary Contact Email</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_main_contact_email" VALUE="<?php echo $rrx_main_contact_email; ?>" maxlength="128">
</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

	<div class="field_title">Primary Contact Phone</div>
	<div class="small_example">e.g. (555) 555-5555</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_main_contact_phone" VALUE="<?php echo $rrx_main_contact_phone; ?>" maxlength="30">

	<div class="field_title">Primary Contact Cell</div>
	<div class="small_example">e.g. (555) 555-5555</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_main_contact_cell" VALUE="<?php echo $rrx_main_contact_cell; ?>" maxlength="30">
	
	<div class="field_title">Primary Contact Fax</div>
	<div class="small_example">e.g. (555) 555-5555</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_main_contact_fax" VALUE="<?php echo $rrx_main_contact_fax; ?>" maxlength="30">

</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

<hr class="clear" />

<div class="rrx-two-column-wrapper">
<table class="noborder">
<tr><td><h1>Signature Name for ReconRx Agreement</h1></td>
<td><input type="checkbox" id="same_contact_authorized" name="same_contact_authorized"><p style="display: inline;">Same as Owner Contact Information</p></td>
</tr>
<tr><td colspan='2'><p>Contract documents will be pre-populated with the name and title entered below for Authorized Signature.</p></td>
</tr>
</table>

<div class="rrx-two-column">

	<div class="field_title">Authorized Signature Name (Full)</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_name" VALUE="<?php echo $rrx_auth_contact_name; ?>" maxlength="100">
	
	<div class="field_title">Authorized Signature Title</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_title" VALUE="<?php echo $rrx_auth_contact_title; ?>" maxlength="100">

	<div class="field_title">Authorized Signature Email</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_email" VALUE="<?php echo $rrx_auth_contact_email; ?>" maxlength="128">

</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

	<div class="field_title">Authorized Signature Phone</div>
	<div class="small_example">e.g. (555) 555-5555</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_auth_contact_phone" VALUE="<?php echo $rrx_auth_contact_phone; ?>" maxlength="30">

	<div class="field_title">Authorized Signature Fax</div>
	<div class="small_example">e.g. (555) 555-5555</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_auth_contact_fax" VALUE="<?php echo $rrx_auth_contact_fax; ?>" maxlength="30">
</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

<hr class="clear" />

<div class="rrx-two-column-wrapper">
<table class="noborder">
<tr><td><h1>Payment Confirmation Contact</h1></td>
<td><input type="checkbox" id="same_contact_pmt" name="same_contact_pmt"><p style="display: inline;">Same as Owner Contact Information</p></td>
</tr>

<tr>
<td colspan='2'><p>The Payment Confirmation Contact will have access to the <?php echo $entity_lc; ?> member's section and will receive fax, email and phone communications regarding third party payments.</p</td>
</tr>
</table>


<div class="rrx-two-column">

	<div class="field_title">Payment Confirmation Name (Full)</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_pmt_name" VALUE="<?php echo $rrx_auth_contact_pmt_name; ?>" maxlength="100">

	<div class="field_title">Payment Confirmation Title</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_pmt_title" VALUE="<?php echo $rrx_auth_contact_pmt_title; ?>" maxlength="100">
	
	<div class="field_title">Payment Confirmation Email</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_pmt_email" VALUE="<?php echo $rrx_auth_contact_pmt_email; ?>" maxlength="128">

</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

	<div class="field_title">Payment Confirmation Phone</div>
	<div class="small_example">e.g. (555) 555-5555</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_auth_contact_pmt_phone" VALUE="<?php echo $rrx_auth_contact_pmt_phone; ?>" maxlength="30">

	<div class="field_title">Payment Confirmation Fax</div>
	<div class="small_example">e.g. (555) 555-5555</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_auth_contact_pmt_fax" VALUE="<?php echo $rrx_auth_contact_pmt_fax; ?>" maxlength="30">
	
</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

<hr class="clear" />

<div class="rrx-two-column-wrapper">
<table class="noborder">
<tr><td><h1>Claim Research Contact</h1></td>
<td><input type="checkbox" id="same_contact_res" name="same_contact_res"><p style="display: inline;">Same as Owner Contact Information</p></td>
</tr>

<tr>
<td colspan='2'><p>The Claim Research Contact will have access to the <?php echo $entity_lc; ?> member's section and will receive fax, email and phone communications regarding claim research.</p</td>
</tr>
</table>


<div class="rrx-two-column">

	<div class="field_title">Claim Research Name (Full)</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_res_name" VALUE="<?php echo $rrx_auth_contact_res_name; ?>" maxlength="100">

	<div class="field_title">Claim Research Title</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_res_title" VALUE="<?php echo $rrx_auth_contact_res_title; ?>" maxlength="100">
	
	<div class="field_title">Claim Research Email</div>
	<INPUT class="rrx-input-text-form required" TYPE="text" NAME="rrx_auth_contact_res_email" VALUE="<?php echo $rrx_auth_contact_res_email; ?>" maxlength="128">

</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

	<div class="field_title">Claim Research Phone</div>
	<div class="small_example">e.g. (555) 555-5555</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_auth_contact_res_phone" VALUE="<?php echo $rrx_auth_contact_res_phone; ?>" maxlength="30">

	<div class="field_title">Claim Research Fax</div>
	<div class="small_example">e.g. (555) 555-5555</div>
	<INPUT class="rrx-input-text-form required phone" TYPE="text" NAME="rrx_auth_contact_res_fax" VALUE="<?php echo $rrx_auth_contact_res_fax; ?>" maxlength="30">
	
</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

<hr class="clear" />

<h1>Additional Information</h1>

<div class="rrx-two-column-wrapper">

<div class="rrx-two-column">

		<div class="field_title">How did you hear about us?</div>
		<select name="rrx_how_did_you_hear_about_us" id="rrx_how_did_you_hear_about_us" class="rrx-input-text-form required">
		<?php 
		if ($rrx_how_did_you_hear_about_us == "") {
			echo "<option value=\"\" selected></option>";
		} else {
			echo "<option value=\"$rrx_how_did_you_hear_about_us\" selected>$rrx_how_did_you_hear_about_us</option>";
		} 
		
		$sql = "
		SELECT Vals FROM officedb.opts 
		WHERE OPTS_ID = 4000 #OPTSEnrollSource
		ORDER BY Vals ASC
		";
		if ($pull = $mysqli->query("$sql")) {
			while ($row = $pull->fetch_assoc()) {
				$options_string = $row['Vals'];
			}
			$options_string = str_replace('"', "", $options_string);
			$options_array = preg_split("/, |,/", $options_string);
			asort($options_array);
			foreach ($options_array as $option) {
		          $selected = '';
                          if($caller == 'GR') {
		            if($option != 'Guaranteed Returns') {continue;}
		            $selected = "selected='selected'";
	        	  }
			  elseif($caller == 'Ontime') {
		            if($option != 'Ontime Soft') {continue;}
		            $selected = "selected='selected'";
	        	  }
			  elseif($caller == 'Onpoint') {
		            if($option != 'Onpoint') {continue;}
		            $selected = "selected='selected'";
	        	  }
			  elseif($caller == 'GeriMed') {
		            if($option != 'GeriMed') {continue;}
		            $selected = "selected='selected'";
	        	  }
			  elseif($caller == 'OneroRx') {
		            if($option != 'OneroRx') {continue;}
		            $selected = "selected='selected'";
	        	  }
			  elseif($caller == 'Atlanticare') {
		            if($option != 'Atlanticare') {continue;}
		            $selected = "selected='selected'";
	        	  }
			  elseif($caller == 'RiteAid') {
		            if($option != 'RiteAid') {continue;}
		            $selected = "selected='selected'";
	        	  }
			  elseif($caller == 'Hometown') {
		            if($option != 'Hometown') {continue;}
		            $selected = "selected='selected'";
	        	  }
			  elseif($caller == 'LeaderNet') {
		            if($option != 'LeaderNet') {continue;}
		            $selected = "selected='selected'";
	        	  }
	        	  else {
	        	    if($option == 'Guaranteed Returns') {continue;}
	        	    if($option == 'Ontime Soft') {continue;}
	        	    if($option == 'GeriMed') {continue;}
	        	    if($option == 'OneroRx') {continue;}
	        	    if($option == 'Onpoint') {continue;}
	        	    if($option == 'Atlanticare') {continue;}
	        	    if($option == 'RiteAid') {continue;}
	        	    if($option == 'Hometown') {continue;}
	        	    if($option == 'LeaderNet') {continue;}
			    $caller='';
	        	  }
			  echo "<option $selected value=\"$option\">$option</option>\n";
			}
		}
                if(!$caller) {
		  echo "<option value=\"Other\">Other</option>\n";
		}
		?>
		</select>
	
</div> <!-- rrx-two-column -->

<div class="rrx-two-column">

		<div class="field_title">Promo Code*</div>
		<INPUT class="rrx-input-text-form" TYPE="text" NAME="rrx_promo_code" ID="rrx_promo_code" VALUE="<?php echo $promo; ?>" maxlength="255">
		
		<p>* If you received a promo code please enter it here. It will be reviewed by our staff on completion of the enrollment.</p>

</div> <!-- rrx-two-column -->

</div> <!-- end rrx-two-column-wrapper -->

<hr class="clear" />
<p class="clear" style="float: left;">Clicking "Submit and Send Contracts" will generate your agreement packet, this could take up to 30 seconds so please be patient waiting for the next page to load.</p>

<div id="errors" style="color: #F00;"></div>

<p class="clear" style="float: left;"><INPUT class="button-form" TYPE="submit" VALUE="Submit and Send Contracts" onclick="return checkRequiredFields(this)" style="width: 300px;"></p>

</div><!-- end mainbody_front -->

<!-- Sidebar -------------------------------------------------------->
<div id="sidebarWrapper">
<div id="sidebar">
<h2>Contact</h2>
<p>Phone: (888) 255-6526</p>
<p>Email: 
RECON@TDSClinical.com
</p>
<h2>Need some help?</h2>
<p>If at any time you need assistance completing this enrollment, please call or send us an email at the contacts listed above.</p>
<br />
</div> <!-- end sidebarWrapper -->
</div> <!-- end sidebar -->
<!------------------------------------------------------------------->
<script>

<?php		
if ( $rrx_ncpdp == "" ) {
  echo '$( "input" ).prop( "disabled", true );';
  echo '$( "select" ).prop( "disabled", true );';
  echo '$("[name=\'rrx_ncpdp\']").prop("disabled", false);';
}
?>

  $('#NCPDP').on('keypress', function(ev) {
    var keyCode = window.event ? ev.keyCode : ev.which;
    //codes for 0-9
    if (keyCode < 48 || keyCode > 57) {
        //codes for backspace, delete, enter
        if (keyCode != 0 && keyCode != 8 && keyCode != 13 && !ev.ctrlKey) {
            ev.preventDefault();
        }
    }
  });

  $('#NPI').on('keypress', function(ev) {
    var keyCode = window.event ? ev.keyCode : ev.which;
    //codes for 0-9
    if (keyCode < 48 || keyCode > 57) {
        //codes for backspace, delete, enter
        if (keyCode != 0 && keyCode != 8 && keyCode != 13 && !ev.ctrlKey) {
            ev.preventDefault();
        }
    }
  });

  function checkNCPDP(val,caller,promo) {
    if(val.length == '7'){
      $.ajax({
        type: 'POST',
        url: '/ajax/pharmacy_data.pl',
        data: { 'ncpdp': val },
        success: function(res) {
        var regex = /[0-9]/g;
        var found = res.result.match(regex);
	var checked;
	if (res.result.match(regex)) {
	  if((res.recon_sts != null || res.recon_sts_cl != null)) {
            var yesno = confirm("This pharmacy is already in our system. Would you like to change the ownership?");
	    if(yesno) {
	      document.getElementById("coo").value = yesno;
  	      document.getElementById("PharmName").value    = res.name;
	      document.getElementById("Address").value      = res.address;
	      document.getElementById("City").value         = res.city;
	      document.getElementById("State").value        = res.state;
	      document.getElementById("Zip").value          = res.zip;
              $( "input" ).prop( "disabled", false );
              $( "select" ).prop( "disabled", false );

              if(caller.match(/GR|Ontime|GeriMed|OneroRx|Atlanticare|RiteAid|Hometown|LeaderNet|Onpoint/)) {
                $("#rrx_how_did_you_hear_about_us").prop("disabled", true);
	      }
	      if (promo) {
                $("#rrx_promo_code").prop("disabled", true);
	      }
	    }
	    else {
              document.getElementById("NCPDP").value = '';	
	    }
	  }
	  else {
            $( "input" ).prop( "disabled", false );
            $( "select" ).prop( "disabled", false );
            if(caller.match(/GR|Ontime|GeriMed|OneroRx|Atlanticare|RiteAid|Hometown|LeaderNet|Onpoint/)) {
              $("#rrx_how_did_you_hear_about_us").prop("disabled", true);
	    }
	    if (promo)  {
              $("#rrx_promo_code").prop("disabled", true);
	    }
	  }
	}
	else {
	  document.getElementById("coo").value = '';
	}
      },
        error: function() {alert("Could not connect to the Server.");}
      });
    }
  }

  document.getElementById("NCPDP").focus();

</script>

</form>
<!--Footer----------------------------------------------------------->
</div><!-- end content_container_front -->
<?php include 'includes/footer.php'; ?>
<!------------------------------------------------------------------->

</div>

<?php 
$mysqli->close();
?>

</body>
</html>
